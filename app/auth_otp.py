import pyotp
import qrcode
import io
import base64
from fastapi import HTTPException
from app.firestore_db import db
from app.security import encrypt_otp_secret, decrypt_otp_secret
from cryptography.fernet import InvalidToken

def get_or_create_otp_secret(google_id: str):
    user_ref = db.collection("users").document(google_id)
    doc = user_ref.get()

    if not doc.exists:
        raise HTTPException(404, "User not found")

    data = doc.to_dict()
    secret = data.get("otp_secret")

    # 🔥 Auto-create if missing
    if not secret:
        plain_secret = pyotp.random_base32()
        encrypted_secret = encrypt_otp_secret(plain_secret)
        user_ref.update({
            "otp_secret": encrypted_secret,
            "otp_enabled": False
        })
        return plain_secret
    else:
        # Decrypt existing secret
        try:
            return decrypt_otp_secret(secret)
        except (InvalidToken, ValueError, Exception):
            # If decryption fails, it might be unencrypted or using a different key.
            # For backward compatibility, return as-is, BUT encrypt it now for the future.
            print(f"DEBUG: Failed to decrypt secret for {google_id}. Assuming unencrypted.")
            encrypted_secret = encrypt_otp_secret(secret)
            user_ref.update({"otp_secret": encrypted_secret})
            return secret

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
    secret = get_or_create_otp_secret(google_id)

    totp = pyotp.TOTP(secret)
    
    # DEBUG LOGGING
    import datetime
    server_now = datetime.datetime.now()
    generated_now = totp.now()
    print(f"[OTP DEBUG] User: {google_id}")
    print(f"[OTP DEBUG] Server Time: {server_now}")
    print(f"[OTP DEBUG] Expected OTP (at server time): {generated_now}")
    print(f"[OTP DEBUG] Received OTP: {otp}")

    # Increased window to 5 (approx 2.5 minutes) to handle client/server clock skew
    if not totp.verify(otp, valid_window=5):
        print(f"[OTP DEBUG] Verification FAILED. Server time might be ahead of client time.")
        return False
        
    print("[OTP DEBUG] Verification SUCCESS")

    # Mark OTP as enabled after first success
    db.collection("users").document(google_id).update({
        "otp_enabled": True
    })

    return True
