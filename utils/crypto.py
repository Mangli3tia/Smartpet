"""MQTT payload encryption using only Python standard library (no pip install needed).

Uses AES-like encryption via pycrypto primitives available in hashlib/hmac/os.
Algorithm: PBKDF2 key derivation + SHA-256 stream cipher + HMAC authentication.
"""
import hashlib
import hmac
import os
import base64


def _derive_keys(master_key: bytes, salt: bytes) -> tuple:
    """Derive enc + auth keys from master key via PBKDF2."""
    material = hashlib.pbkdf2_hmac("sha256", master_key, salt, 100_000, dklen=64)
    return material[:32], material[32:]


def encrypt(plaintext: str, key: bytes) -> str:
    """Encrypt a string, return base64-encoded ciphertext (salt + iv + ciphertext + mac)."""
    salt = os.urandom(16)
    iv = os.urandom(16)
    enc_key, mac_key = _derive_keys(key, salt)

    # XOR stream cipher: keystream = SHA-256(enc_key + iv + counter)
    plain_bytes = plaintext.encode("utf-8")
    cipher_bytes = bytearray()
    counter = 0
    while len(cipher_bytes) < len(plain_bytes):
        block = hashlib.sha256(enc_key + iv + counter.to_bytes(4, "big")).digest()
        for b in block:
            if len(cipher_bytes) >= len(plain_bytes):
                break
            cipher_bytes.append(b)
        counter += 1

    # XOR
    encrypted = bytes(a ^ p for a, p in zip(cipher_bytes, plain_bytes))

    # HMAC for authentication
    packed = salt + iv + encrypted
    mac = hmac.new(mac_key, packed, "sha256").digest()

    return base64.b64encode(packed + mac).decode("utf-8")


def decrypt(ciphertext: str, key: bytes) -> str:
    """Decrypt a base64-encoded ciphertext back to the original string."""
    raw = base64.b64decode(ciphertext.encode("utf-8"))

    salt = raw[:16]
    iv = raw[16:32]
    mac = raw[-32:]
    encrypted = raw[32:-32]

    enc_key, mac_key = _derive_keys(key, salt)

    # Verify HMAC
    expected_mac = hmac.new(mac_key, raw[:-32], "sha256").digest()
    if not hmac.compare_digest(mac, expected_mac):
        raise ValueError("Message authentication failed — data may be tampered")

    # XOR stream cipher (same keystream generation)
    cipher_bytes = bytearray()
    counter = 0
    while len(cipher_bytes) < len(encrypted):
        block = hashlib.sha256(enc_key + iv + counter.to_bytes(4, "big")).digest()
        for b in block:
            if len(cipher_bytes) >= len(encrypted):
                break
            cipher_bytes.append(b)
        counter += 1

    decrypted = bytes(a ^ p for a, p in zip(cipher_bytes, encrypted))
    return decrypted.decode("utf-8")
