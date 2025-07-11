from Crypto.Cipher import AES
import base64
from app.core import config


def encrypt_private_key(private_key_hex: str) -> str:
    aes_key = bytes.fromhex(config.AES_KEY)

    cipher = AES.new(aes_key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(bytes.fromhex(private_key_hex[2:]))
    return base64.b64encode(cipher.nonce + tag + ciphertext).decode()
