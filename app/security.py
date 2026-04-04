import hashlib
import bcrypt
import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

# Fernet (AES) Key
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    # Fallback or error (better to error out in production)
    print("WARNING: ENCRYPTION_KEY not found in .env. TOTP secrets will NOT be secure.")
    # For now, we will expect it to be there. 
    # If it's missing, let's generate one temporarily for this session if needed, 
    # but the user should set it.
    ENCRYPTION_KEY = Fernet.generate_key()

cipher_suite = Fernet(ENCRYPTION_KEY)

def _prehash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def hash_password(password: str) -> str:
    # bcrypt works with bytes
    prehashed = _prehash(password).encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(prehashed, salt).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    prehashed = _prehash(password).encode("utf-8")
    # hashed comes as string, bcrypt needs bytes
    return bcrypt.checkpw(prehashed, hashed.encode("utf-8"))

def encrypt_otp_secret(secret: str) -> str:
    """Encrypts a TOTP secret using AES (Fernet)."""
    return cipher_suite.encrypt(secret.encode()).decode()

def decrypt_otp_secret(encrypted_secret: str) -> str:
    """Decrypts a TOTP secret using AES (Fernet)."""
    return cipher_suite.decrypt(encrypted_secret.encode()).decode()
