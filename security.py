import os
import sys
from cryptography.fernet import Fernet

if getattr(sys, 'frozen', False):
    APP_PATH = os.path.dirname(sys.executable)
else:
    APP_PATH = os.path.dirname(os.path.abspath(__file__))

KEY_FILE = os.path.join(APP_PATH, 'secret.key')

def load_key():
    """
    Load the previously generated key. If not exists, generate one.
    """
    if not os.path.exists(KEY_FILE):
        generate_key()
    
    with open(KEY_FILE, 'rb') as key_file:
        return key_file.read()

def generate_key():
    """
    Generates a key and saves it into a file
    """
    key = Fernet.generate_key()
    with open(KEY_FILE, 'wb') as key_file:
        key_file.write(key)

def encrypt_password(password: str) -> str:
    """
    Encrypts a password using the loaded key.
    """
    key = load_key()
    f = Fernet(key)
    encrypted_password = f.encrypt(password.encode())
    return encrypted_password.decode()

def decrypt_password(encrypted_password: str) -> str:
    """
    Decrypts an encrypted password using the loaded key.
    """
    if not encrypted_password:
        return ""
    try:
        key = load_key()
        f = Fernet(key)
        decrypted_password = f.decrypt(encrypted_password.encode())
        return decrypted_password.decode()
    except Exception as e:
        print(f"Decryption error: {e}")
        return ""
