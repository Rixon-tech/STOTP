from fastapi import HTTPException
from app.firestore_db import db
from app.security import verify_password

def verify_admin_password(google_id: str, password: str):
    user_ref = db.collection("users").document(google_id)
    doc = user_ref.get()

    if not doc.exists:
        print(f"DEBUG: User {google_id} not found in Firestore.")
        raise HTTPException(403, "User not registered by admin")

    data = doc.to_dict()

    if not data.get("created_by_admin"):
        print(f"DEBUG: User {google_id} found but 'created_by_admin' is false/missing.")
        raise HTTPException(403, "Admin approval required")

    if not verify_password(password, data["app_password_hash"]):
        print("DEBUG: Password verification failed.")
        raise HTTPException(401, "Invalid application password")

    return data

def verify_manager_login(email: str, password: str):
    """Verifies manager login using email and password (no Google token required)."""
    users_ref = db.collection("users")
    query = users_ref.where("email", "==", email).limit(1).get()

    if not query:
        raise HTTPException(401, "Invalid manager credentials")

    data = query[0].to_dict()
    data["sub"] = query[0].id

    if data.get("role") != "manager":
        raise HTTPException(403, "Access restricted to managers only")

    if not verify_password(password, data["app_password_hash"]):
        raise HTTPException(401, "Invalid manager password")

    return data