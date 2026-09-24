"""Encrypt a short advisory before placing it in a public repository artifact."""

import hashlib
import os

from nacl.secret import SecretBox


PREFIX = b"signal-v1:"


def _key(password, salt):
    if not password or len(password) < 20:
        raise ValueError("La clave compartida debe tener al menos 20 caracteres")
    return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=SecretBox.KEY_SIZE)


def seal(message, password):
    salt = os.urandom(16)
    return PREFIX + salt + SecretBox(_key(password, salt)).encrypt(message.encode("utf-8"))


def open_message(blob, password):
    if not blob.startswith(PREFIX) or len(blob) < len(PREFIX) + 16 + 24 + 16:
        raise ValueError("Resultado cifrado inválido")
    salt = blob[len(PREFIX):len(PREFIX) + 16]
    return SecretBox(_key(password, salt)).decrypt(blob[len(PREFIX) + 16:]).decode("utf-8")
