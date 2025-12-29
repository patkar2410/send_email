import sys
import os
import shutil
import logging
import smtplib
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                               QFileDialog, QCheckBox, QProgressBar, QTextEdit, 
                               QMessageBox, QDialog, QFormLayout, QGroupBox,
                               QStyle, QTableWidget, QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt, QThread, Signal
from config_manager import ConfigManager
from logger_manager import LoggerManager
from email_sender import EmailSender

class ConfigDialog(QDialog):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SMTP Configuration")
        self.config_manager = config_manager
        self.resize(400, 300)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        current_config = self.config_manager.get_smtp_config()

        self.server_input = QLineEdit(current_config.get('server', ''))
        self.port_input = QLineEdit(current_config.get('port', '587'))
        self.email_input = QLineEdit(current_config.get('email', ''))
        
        # Password field with toggle
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        
        # Pre-fill if password exists (decrypted for viewing if requested, but better to keep hidden by default)
        # We don't pre-fill the text because we only want to update if user types something new? 
        # Requirement: "if the password is existing in config.ini file, give an option to view the password"
        # So we should pre-fill it.
        existing_pass = self.config_manager.get_decrypted_password()
        if existing_pass:
            self.password_input.setText(existing_pass)
        else:
            self.password_input.setPlaceholderText("Enter new password")

        self.show_pass_check = QCheckBox("Show Password")
        self.show_pass_check.stateChanged.connect(self.toggle_password_visibility)
        
        self.tls_check = QCheckBox()
        self.tls_check.setChecked(current_config.get('use_tls', 'true').lower() == 'true')
        
        self.ssl_check = QCheckBox()
        self.ssl_check.setChecked(current_config.get('use_ssl', 'false').lower() == 'true')

        form_layout.addRow("SMTP Server:", self.server_input)
        form_layout.addRow("Port:", self.port_input)
        form_layout.addRow("Sender Email:", self.email_input)
        form_layout.addRow("Password:", self.password_input)
        form_layout.addRow("", self.show_pass_check) # Align with password field
        form_layout.addRow("Use TLS:", self.tls_check)
        form_layout.addRow("Use SSL:", self.ssl_check)

        layout.addLayout(form_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        test_btn = QPushButton("Test Connection")
        test_btn.clicked.connect(self.test_connection)
        
        save_btn = QPushButton("Save Configuration")
        save_btn.clicked.connect(self.save_config)
        
        btn_layout.addWidget(test_btn)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def toggle_password_visibility(self, state):
        if state == Qt.Checked:
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)

    def test_connection(self):
        server = self.server_input.text()
        port = self.port_input.text()
        email = self.email_input.text()
        password = self.password_input.text()
        use_tls = self.tls_check.isChecked()
        use_ssl = self.ssl_check.isChecked()
        
        if not server or not port or not email or not password:
             QMessageBox.warning(self, "Missing Info", "Please fill in all fields to test connection.")
             return

        try:
            # Perform a test connection
            if use_ssl:
                smtp = smtplib.SMTP_SSL(server, int(port), timeout=10)
            else:
                smtp = smtplib.SMTP(server, int(port), timeout=10)
            
            smtp.set_debuglevel(1)
            
            smtp.ehlo()
            if use_tls and not use_ssl:
                smtp.starttls()
                smtp.ehlo()
            
            smtp.login(email, password)
            smtp.quit()
            
            QMessageBox.information(self, "Success", "Connection successful! Credentials are valid.")
            
        except Exception as e:
             QMessageBox.critical(self, "Connection Failed", f"Could not connect to SMTP server.\n\nError: {str(e)}")

    def save_config(self):
        server = self.server_input.text()
        port = self.port_input.text()
        email = self.email_input.text()
        password = self.password_input.text()
        use_tls = self.tls_check.isChecked()
        use_ssl = self.ssl_check.isChecked()

        try:
            self.config_manager.update_smtp_config(server, port, email, password, use_tls, use_ssl)
            QMessageBox.information(self, "Success", "Configuration saved successfully!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {str(e)}")

class EmailWorker(QThread):
    progress_signal = Signal(int)
    log_signal = Signal(str)
    status_signal = Signal(str, str) # filename, status
    finished_signal = Signal()
    
    def __init__(self, file_list, recipient_email, config_manager, logger_manager):
        super().__init__()
        self.file_list = file_list
        self.recipient_email = recipient_email
        self.config_manager = config_manager
        self.logger_manager = logger_manager
        self.is_running = True

    def run(self):
        email_sender = EmailSender(self.config_manager)
        total_files = len(self.file_list)
        
        for i, file_path in enumerate(self.file_list):
            if not self.is_running:
                break
            
            filename = os.path.basename(file_path)
            self.log_signal.emit(f"Processing {filename}...")
            
            try:
                email_sender.send_email(self.recipient_email, file_path)
                self.logger_manager.log_delivery_status(filename, self.recipient_email, True)
                self.log_signal.emit(f"SUCCESS: Sent {filename}")
                self.status_signal.emit(filename, "SENT")
            except Exception as e:
                error_msg = str(e)
                self.logger_manager.log_delivery_status(filename, self.recipient_email, False, error_msg)
                self.log_signal.emit(f"FAILURE: Could not send {filename}. Error: {error_msg}")
                self.status_signal.emit(filename, "FAILED")
            
            self.progress_signal.emit(int((i + 1) / total_files * 100))
        
        self.finished_signal.emit()

    def stop(self):
        self.is_running = False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Batch Email Sender")
        self.resize(800, 600)
        
        self.config_manager = ConfigManager()
        self.logger_manager = LoggerManager()
        self.worker = None
        self.file_list = []

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 1. Selection Area
        selection_group = QGroupBox("Input Selection")
        selection_layout = QFormLayout()
        
        # Directory Selection
        dir_layout = QHBoxLayout()
        self.dir_input = QLineEdit()
        self.dir_input.setReadOnly(True)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_directory)
        dir_layout.addWidget(self.dir_input)
        dir_layout.addWidget(browse_btn)
        
        # Email Input
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("recipient1@example.com, recipient2@example.com")
        
        selection_layout.addRow(QLabel("Select Directory"))
        selection_layout.addRow(dir_layout)
        selection_layout.addRow(QLabel("Recipient Email"))
        selection_layout.addRow(self.email_input)
        selection_group.setLayout(selection_layout)
        main_layout.addWidget(selection_group)

        # 2. Controls
        controls_layout = QHBoxLayout()
        
        config_btn = QPushButton("Edit SMTP Config")
        config_btn.clicked.connect(self.open_config)
        
        self.debug_check = QCheckBox("Enable Debug Logging")
        self.debug_check.stateChanged.connect(self.toggle_debug)
        
        self.send_btn = QPushButton("SEND EMAILS")
        self.send_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        self.send_btn.clicked.connect(self.start_sending)
        self.send_btn.setEnabled(False) # Disabled until files selected

        controls_layout.addWidget(config_btn)
        controls_layout.addWidget(self.debug_check)
        controls_layout.addStretch()
        controls_layout.addWidget(self.send_btn)
        
        main_layout.addLayout(controls_layout)

        # 3. Dashboard
        dashboard_group = QGroupBox("Status Dashboard")
        dashboard_layout = QHBoxLayout() # Changed to Horizontal
        
        # Left Column: Progress & Table
        left_layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        
        self.status_table = QTableWidget()
        self.status_table.setColumnCount(2)
        self.status_table.setHorizontalHeaderLabels(["Filename", "Status"])
        self.status_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.status_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.status_table.setColumnWidth(1, 100)
        
        left_layout.addWidget(QLabel("File Status:"))
        left_layout.addWidget(self.status_table)
        left_layout.addWidget(QLabel("Overall Progress:"))
        left_layout.addWidget(self.progress_bar)
        
        # Right Column: Log
        right_layout = QVBoxLayout()
        self.log_viewer = QTextEdit()
        self.log_viewer.setReadOnly(True)
        
        right_layout.addWidget(QLabel("Activity Log:"))
        right_layout.addWidget(self.log_viewer)
        
        # Add columns to main dashboard layout
        dashboard_layout.addLayout(left_layout, 1) # Stretch factor 1
        dashboard_layout.addLayout(right_layout, 1) # Stretch factor 1
        
        dashboard_group.setLayout(dashboard_layout)
        main_layout.addWidget(dashboard_group)

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.dir_input.setText(directory)
            self.scan_directory(directory)

    def scan_directory(self, directory):
        try:
            # Get all files (filtering out directories)
            self.file_list = [os.path.join(directory, f) for f in os.listdir(directory) 
                              if os.path.isfile(os.path.join(directory, f)) and not f.startswith('.')]
            
            if not self.file_list:
                QMessageBox.warning(self, "No Files", "No files found in the selected directory.")
                self.send_btn.setEnabled(False)
                return

            self.log_viewer.append(f"Found {len(self.file_list)} files.")
            self.log_viewer.append("Initializing Audit Log...")
            
            # Populate Table
            self.status_table.setRowCount(len(self.file_list))
            for row, file_path in enumerate(self.file_list):
                filename = os.path.basename(file_path)
                self.status_table.setItem(row, 0, QTableWidgetItem(filename))
                self.status_table.setItem(row, 1, QTableWidgetItem("PENDING"))
            
            # Create Audit Log
            log_path = self.logger_manager.create_audit_log([os.path.basename(f) for f in self.file_list])
            self.log_viewer.append(f"Audit Log created: {log_path}")
            
            self.send_btn.setEnabled(True)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error scanning directory: {str(e)}")
            self.file_list = []
            self.send_btn.setEnabled(False)

    def open_config(self):
        dialog = ConfigDialog(self.config_manager, self)
        dialog.exec()

    def toggle_debug(self, state):
        self.logger_manager.set_debug_mode(state == Qt.Checked)
        self.log_viewer.append(f"Debug mode {'enabled' if state == Qt.Checked else 'disabled'}.")

    def start_sending(self):
        recipient = self.email_input.text()
        if not recipient:
            QMessageBox.warning(self, "Validation Error", "Please enter a recipient email address.")
            return

        if not self.file_list:
            return

        # Disable controls
        self.send_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.log_viewer.append("Starting email delivery...")

        # Start Worker
        self.worker = EmailWorker(self.file_list, recipient, self.config_manager, self.logger_manager)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.log_signal.connect(self.update_log)
        self.worker.status_signal.connect(self.update_status)
        self.worker.finished_signal.connect(self.sending_finished)
        self.worker.start()

    def update_progress(self, val):
        self.progress_bar.setValue(val)

    def update_log(self, message):
        self.log_viewer.append(message)
        
    def update_status(self, filename, status):
        # Find row with filename
        # Since we populated in order, we could assume order, but searching is safer if list changes (it shouldn't here)
        # Optimization: worker could send row index. But search is fine for < 10000 files.
        items = self.status_table.findItems(filename, Qt.MatchExactly)
        if items:
            row = items[0].row()
            self.status_table.setItem(row, 1, QTableWidgetItem(status))
            # Optional: Color coding
            if status == "SENT":
                self.status_table.item(row, 1).setBackground(Qt.green)
            elif status == "FAILED":
                self.status_table.item(row, 1).setBackground(Qt.red)

    def sending_finished(self):
        self.send_btn.setEnabled(True)
        self.log_viewer.append("Processing complete.")
        QMessageBox.information(self, "Done", "Email processing finished. Check audit log for details.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
