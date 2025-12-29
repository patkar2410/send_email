import configparser
import os
import sys
from security import encrypt_password, decrypt_password

if getattr(sys, 'frozen', False):
    APP_PATH = os.path.dirname(sys.executable)
else:
    APP_PATH = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(APP_PATH, 'config.ini')

class ConfigManager:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.load_config()

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            # Create default if not exists
            self.config['SMTP'] = {
                'server': 'smtp.gmail.com',
                'port': '587',
                'email': '',
                'password': '',
                'use_tls': 'true',
                'use_ssl': 'false'
            }
            self.save_config()
        else:
            self.config.read(CONFIG_FILE)

    def save_config(self):
        with open(CONFIG_FILE, 'w') as configfile:
            self.config.write(configfile)

    def get_smtp_config(self):
        return self.config['SMTP']

    def update_smtp_config(self, server, port, email, password, use_tls, use_ssl):
        self.config['SMTP']['server'] = server
        self.config['SMTP']['port'] = str(port)
        self.config['SMTP']['email'] = email
        
        # If password is provided (not empty), encrypt it. 
        # If it's the same as existing encrypted one, leave it (but here we get raw input usually).
        # We assume the UI passes the raw password if it changed, or we need to handle that logic.
        # For simplicity: Always encrypt what is passed if it doesn't look like it's already encrypted?
        # Actually, best practice: UI sends raw password. We encrypt and store.
        # When reading, we decrypt.
        
        if password:
             # Basic check to avoid double encryption if UI passes back encrypted string (unlikely but possible)
             # But here we assume 'password' argument is the new raw password from user input.
             self.config['SMTP']['password'] = encrypt_password(password)
        
        self.config['SMTP']['use_tls'] = str(use_tls)
        self.config['SMTP']['use_ssl'] = str(use_ssl)
        self.save_config()

    def get_decrypted_password(self):
        encrypted = self.config['SMTP'].get('password', '')
        return decrypt_password(encrypted)
