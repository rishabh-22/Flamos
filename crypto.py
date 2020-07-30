import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

salt = b'\x99!o\xf1\x95\xc7-V\xecg\xd7I{,[\x13'


def generate_key_from_password(password):
    password = password.encode()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    return key


def encrypt_message(message, key):
    f = Fernet(key)
    message = message.encode()
    encryption = f.encrypt(message)
    return encryption


def decrypt_message(encryption, key):
    f = Fernet(key)
    message = f.decrypt(encryption)
    return message.decode()
