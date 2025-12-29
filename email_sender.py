import smtplib
import os
import mimetypes
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from config_manager import ConfigManager
import logging

class EmailSender:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager

    @retry(
        stop=stop_after_attempt(3), 
        wait=wait_fixed(5),
        retry=retry_if_exception_type((smtplib.SMTPException, OSError))
    )
    def send_email(self, to_email, file_path):
        """
        Sends an email with the specified file as attachment.
        Retries 3 times with 5 seconds wait on failure.
        """
        smtp_config = self.config_manager.get_smtp_config()
        smtp_server = smtp_config.get('server')
        smtp_port = int(smtp_config.get('port', 587))
        sender_email = smtp_config.get('email')
        
        # Get decrypted password
        sender_password = self.config_manager.get_decrypted_password()
        
        use_tls = smtp_config.get('use_tls', 'true').lower() == 'true'
        use_ssl = smtp_config.get('use_ssl', 'false').lower() == 'true'

        if not sender_email or not sender_password:
            raise ValueError("Email credentials are not configured properly.")

        msg = MIMEMultipart()
        msg['From'] = sender_email
        
        # Handle multiple recipients
        if isinstance(to_email, list):
            recipients = to_email
            msg['To'] = ", ".join(to_email)
        else:
            # Split by comma and strip whitespace
            recipients = [e.strip() for e in to_email.split(',') if e.strip()]
            msg['To'] = to_email
            
        filename = os.path.basename(file_path)
        msg['Subject'] = filename
        
        body = f"Please find the attached file: {filename}"
        msg.attach(MIMEText(body, 'plain'))

        # Attachment
        try:
            with open(file_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {filename}",
            )
            msg.attach(part)
        except Exception as e:
            logging.error(f"Failed to read file {file_path}: {e}")
            raise e

        # Sending
        try:
            logging.debug(f"Connecting to SMTP server: {smtp_server}:{smtp_port} (SSL: {use_ssl}, TLS: {use_tls})")
            
            if use_ssl:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            else:
                server = smtplib.SMTP(smtp_server, smtp_port)
                
            server.set_debuglevel(1 if logging.getLogger().getEffectiveLevel() == logging.DEBUG else 0)
            
            # Identify to server
            code, response = server.ehlo()
            logging.debug(f"EHLO response: {code} {response}")
            
            if use_tls and not use_ssl:
                logging.debug("Starting TLS...")
                server.starttls()
                code, response = server.ehlo() # Re-identify after TLS
                logging.debug(f"EHLO (after TLS) response: {code} {response}")
            
            # Verify connection
            code, response = server.noop()
            if code != 250:
                 logging.warning(f"NOOP check failed: {code} {response}")
            else:
                 logging.debug("Connection verified (NOOP OK).")

            logging.debug(f"Logging in as {sender_email}...")
            server.login(sender_email, sender_password)
            
            text = msg.as_string()
            logging.debug(f"Sending email to {recipients}...")
            
            # sendmail returns a dict of failed recipients, empty if all success
            failed_recipients = server.sendmail(sender_email, recipients, text)
            
            server.quit()
            
            if failed_recipients:
                error_msg = f"Failed to send to some recipients: {failed_recipients}"
                logging.error(error_msg)
                raise smtplib.SMTPException(error_msg)
                
            logging.info(f"Email sent successfully to {recipients} for file {filename}")
            return True
        except Exception as e:
            logging.error(f"Failed to send email for {filename}: {e}")
            raise e
