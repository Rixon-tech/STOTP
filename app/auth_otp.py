import pyotp
import qrcode
import io
import base64
import time
from fastapi import HTTPException
from app.firestore_db import db
from app.security import encrypt_otp_secret, decrypt_otp_secret
from cryptography.fernet import InvalidToken

def get_otp_secret(google_id: str, auto_create: bool = False, email: str = None):
    """
    Safely retrieves the OTP secret. If corrupted, returns None to trigger re-setup.
    """
    user_ref = db.collection("users").document(google_id)
    doc = user_ref.get()

    if not doc.exists:
        if auto_create and email:
            plain_secret = pyotp.random_base32()
            user_ref.set({
                "email": email,
                "created_at": time.time(),
                "otp_secret": encrypt_otp_secret(plain_secret),
                "otp_enabled": False,
                "role": "user"
            })
            return plain_secret
        return None

    data = doc.to_dict()
    secret = data.get("otp_secret")

    if not secret or secret == "":
        if auto_create:
            plain_secret = pyotp.random_base32()
            user_ref.update({"otp_secret": encrypt_otp_secret(plain_secret)})
            return plain_secret
        return None

    # Retrieve and Clean
    secret = str(secret).strip()
    try:
        # 1. Try current decryption (Legacy fallback inside security.py)
        plain = decrypt_otp_secret(secret)
    except Exception:
        # 2. Fallback: Check if it's already plain Base32
        import re
        if re.match(r'^[A-Z2-7]{16,64}$', secret, re.IGNORECASE):
            plain = secret
        else:
            print(f"CRITICAL: Secret for {google_id} is unreadable.")
            user_ref.update({"otp_secret": None, "otp_enabled": False})
            return None

    # Final sanity check for pyotp
    if not all(c.upper() in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567=' for c in plain):
        print(f"CRITICAL: Decrypted secret for {google_id} contains invalid Base32 digits.")
        user_ref.update({"otp_secret": None, "otp_enabled": False})
        return None
        
    return plain


def generate_qr_code(email: str, secret: str):
    uri = pyotp.TOTP(secret).provisioning_uri(
        name=email,
        issuer_name="SmartLockSystem"
    )
    
    qr = qrcode.make(uri)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    
    return base64.b64encode(buf.getvalue()).decode()

def verify_user_otp(google_id: str, otp: str):
    # CRITICAL: We pass auto_create=False here to prevent accidental secret changes during log-in
    secret = get_otp_secret(google_id, auto_create=False)
    if not secret:
        print(f"[OTP] FAILURE: No valid secret found for {google_id}")
        return False
        
    totp = pyotp.TOTP(secret)
    server_now = int(time.time())
    
    # Check current window + standard grace period
    if totp.verify(otp, for_time=server_now, valid_window=3):
        print(f"[OTP] SUCCESS | User: {google_id}")
        db.collection("users").document(google_id).update({"otp_enabled": True})
        return True
    else:
        # Fallback: Deep drift search (+/- 4 minutes)
        for offset in range(-240, 241, 30):
            if totp.verify(otp, for_time=server_now + offset, valid_window=0):
                print(f"[OTP] SUCCESS via drift compensation ({offset}s) | User: {google_id}")
                db.collection("users").document(google_id).update({"otp_enabled": True})
                return True
        
        print(f"[OTP] MISMATCH | User: {google_id} | Expected: {totp.at(server_now)}")
        return False


