from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


def get_cipher():
    return Fernet(settings.FERNET_SECRET_KEY.encode('utf-8'))

def encrypt_secret(plaintext: str) -> bytes:
    return get_cipher().encrypt(plaintext.encode('utf-8'))

def decrypt_secret(ciphertext : bytes)-> str:
    try:
        return get_cipher().decrypt(ciphertext).decode('utf-8')
    except InvalidToken:
        raise ValueError("Invalid ciphertext or key.")
