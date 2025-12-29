import os
import sys
import datetime
import logging

if getattr(sys, 'frozen', False):
    APP_PATH = os.path.dirname(sys.executable)
else:
    APP_PATH = os.path.dirname(os.path.abspath(__file__))

LOGS_DIR = os.path.join(APP_PATH, 'LOGS')
DEBUG_LOG = os.path.join(APP_PATH, 'debug.log')

class LoggerManager:
    def __init__(self, debug_mode=False):
        self.log_file_path = None
        self.setup_debug_logging(debug_mode)

    def setup_debug_logging(self, debug_mode):
        level = logging.DEBUG if debug_mode else logging.INFO
        logging.basicConfig(
            filename=DEBUG_LOG,
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filemode='a'
        )

    def create_audit_log(self, file_list):
        if not os.path.exists(LOGS_DIR):
            os.makedirs(LOGS_DIR)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file_path = os.path.join(LOGS_DIR, f"audit_log_{timestamp}.txt")
        
        with open(self.log_file_path, 'w') as f:
            f.write(f"Audit Log created at {datetime.datetime.now()}\n")
            f.write("-" * 50 + "\n")
            f.write("Initial File Status:\n")
            for filename in file_list:
                f.write(f"{filename}: PENDING\n")
            f.write("-" * 50 + "\n")
            f.write("Email Delivery Results:\n")
            f.write(f"{'Timestamp':<20} | {'Filename':<30} | {'Email':<30} | {'Status':<10}\n")
            f.write("-" * 100 + "\n")
            
        logging.info(f"Created audit log: {self.log_file_path}")
        return self.log_file_path

    def log_delivery_status(self, filename, email, status, error_msg=""):
        if not self.log_file_path:
            logging.warning("Attempted to log delivery status but no audit log file is initialized.")
            return

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_str = "SUCCESS" if status else "FAILURE"
        
        log_entry = f"{timestamp:<20} | {filename:<30} | {email:<30} | {status_str:<10}"
        if error_msg:
             log_entry += f" | Error: {error_msg}"
        log_entry += "\n"

        try:
            with open(self.log_file_path, 'a') as f:
                f.write(log_entry)
            logging.info(f"Logged status for {filename}: {status_str}")
        except Exception as e:
            logging.error(f"Failed to write to audit log: {e}")

    def set_debug_mode(self, enabled):
        # Update root logger level
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG if enabled else logging.INFO)
