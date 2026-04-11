import hashlib
import bcrypt
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from dotenv import load_dotenv

load_dotenv()

# Keys
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    print("WARNING: ENCRYPTION_KEY not found in .env. Falling back to temporary key.")
    ENCRYPTION_KEY = Fernet.generate_key().decode()

# AES-256 Key derivation (32 bytes)
AES_KEY = hashlib.sha256(ENCRYPTION_KEY.encode()).digest()
aesgcm = AESGCM(AES_KEY)

# Fernet suite for legacy decryption
cipher_suite = Fernet(ENCRYPTION_KEY)

def _prehash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def hash_password(password: str) -> str:
    prehashed = _prehash(password).encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(prehashed, salt).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    prehashed = _prehash(password).encode("utf-8")
    return bcrypt.checkpw(prehashed, hashed.encode("utf-8"))

def encrypt_otp_secret(secret: str) -> str:
    """Encrypts a TOTP secret using AES-256-GCM."""
    nonce = os.urandom(12)
    # encrypt returns ciphertext + tag
    ciphertext = aesgcm.encrypt(nonce, secret.encode(), None)
    return base64.b64encode(nonce + ciphertext).decode()

def decrypt_otp_secret(encrypted_secret: str) -> str:
    """Decrypts a TOTP secret, trying AES-256-GCM first, then falling back to Fernet."""
    if not encrypted_secret:
        return ""

    # 1. Try AES-256-GCM (New Format)
    try:
        data = base64.b64decode(encrypted_secret.encode())
        nonce = data[:12]
        ciphertext = data[12:]
        return aesgcm.decrypt(nonce, ciphertext, None).decode()
    except Exception:
        pass

    # 2. Try Fernet (Legacy AES-128)
    try:
        return cipher_suite.decrypt(encrypted_secret.encode()).decode()
    except Exception:
        pass
    
    # 3. Try plain text fallback (unsafe, but handles early legacy/corrupted data)
    try:
        # Check if it looks like a Base32 secret (standard TOTP)
        import re
        if re.match(r"^[A-Z2-7]{16,64}$", encrypted_secret):
            return encrypted_secret
    except Exception:
        pass

    raise ValueError("Incompatible or corrupted secret format")