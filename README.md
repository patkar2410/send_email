# Batch Email Sender

A robust desktop application built with Python and PySide6 (Qt) for automating the process of sending files as email attachments. This tool allows you to select a directory of files and send each one individually to specified recipients using your own SMTP server configuration.

## Features

- **User-Friendly GUI**: Clean and intuitive interface built with PySide6.
- **Batch Processing**: Automatically scans a selected directory and processes all files.
- **File Management**: Successfully sent files are automatically moved to a `SENTEMAILS` subdirectory.
- **SMTP Configuration**: Support for custom SMTP servers (Gmail, Outlook, custom domains) with TLS/SSL support.
- **Secure Storage**: Sensitive credentials (passwords) are handled securely using encryption.
- **Resilience**: Built-in retry mechanism (using `tenacity`) for handling network glitches or temporary SMTP errors.
- **Real-time Monitoring**:
  - Progress bar for overall status.
  - Individual file status table (Pending/Sent/Failed).
  - Detailed activity log.
- **Audit Logging**: Generates a detailed audit log of all operations.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd send_email
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running from Source

1. Execute the main script:
   ```bash
   python main.py
   ```

2. **Configure SMTP**:
   - Click "Edit SMTP Config".
   - Enter your SMTP server details (e.g., `smtp.gmail.com` for Gmail).
   - Port (usually 587 for TLS or 465 for SSL).
   - Enter your email and password (or App Password if using Gmail with 2FA).
   - Click "Save Configuration".

3. **Send Emails**:
   - Click "Browse..." to select the directory containing the files you want to send.
   - Enter the recipient email address(es) in the "Recipient Email" field.
   - Click "SEND EMAILS".

### Building the Executable

To create a standalone executable for distribution:

1. Ensure `pyinstaller` is installed (included in requirements).
2. Run the build script or use PyInstaller directly:
   ```bash
   pyinstaller BatchEmailSender.spec
   ```
   *Alternatively, if a `build_exe.py` script is provided, you can run that.*

The executable will be located in the `dist/` directory.

## Project Structure

- `main.py`: Application entry point.
- `gui.py`: Implementation of the main window and UI logic.
- `email_sender.py`: Core logic for handling SMTP connections and sending emails.
- `config_manager.py`: Manages secure storage and retrieval of configuration settings.
- `logger_manager.py`: Handles application logging and audit trails.
- `requirements.txt`: List of Python dependencies.

## License

This project is licensed under the terms of the LICENSE file included in the repository.
