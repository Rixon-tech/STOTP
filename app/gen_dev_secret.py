# generate_device_secret.py
import secrets
import base64

def generate_device_secret(length_bytes=32):
    raw = secrets.token_bytes(length_bytes)
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")

if __name__ == "__main__":
    secret = generate_device_secret()
    print("\n🔐 DEVICE_SECRET (store securely):\n")
    print(secret)
