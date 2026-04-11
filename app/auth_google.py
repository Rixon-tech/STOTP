from fastapi import Header, HTTPException
from google.oauth2 import id_token
from google.auth.transport import requests
from app.config import GOOGLE_CLIENT_ID
from app.firestore_db import db

from fastapi import Header, HTTPException
from google.oauth2 import id_token
from google.auth.transport import requests
from app.config import GOOGLE_CLIENT_ID
from app.firestore_db import db

def verify_google_token(authorization: str):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing authorization token")

    token = authorization.split(" ")[1]

    # --- Support for Direct Manager Login (no Google token) ---
    if token.startswith("MANAGER_"):
        manager_id = token.replace("MANAGER_", "")
        doc = db.collection("users").document(manager_id).get()
        if not doc.exists:
            raise HTTPException(401, "Invalid session")
        
        data = doc.to_dict()
        return {
            "sub": manager_id,
            "email": data.get("email", "manager"),
            "role": data.get("role", "manager"),
            "is_manager": True
        }

    # --- Standard Google Verification ---
    try:
        user_data = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            GOOGLE_CLIENT_ID
        )
        # Fetch role from Firestore for regular users
        doc = db.collection("users").document(user_data["sub"]).get()
        if doc.exists:
            user_data["role"] = doc.to_dict().get("role", "user")
            user_data["exists"] = True
            user_data["otp_enabled"] = doc.to_dict().get("otp_enabled", False)
        else:
            user_data["role"] = "user"
            user_data["exists"] = False
            user_data["otp_enabled"] = False

        return user_data
    except Exception:
        raise HTTPException(401, "Invalid Google token")