import hashlib
import bcrypt
from google.cloud import firestore
from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_file(
    "service_account.json"
)

db = firestore.Client(credentials=credentials)

user_id = "102421812802450513314"
new_password = "John@2255"

user_ref = db.collection("users").document(user_id)

print(f"Updating password for user {user_id}...")

def _prehash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def hash_password(password: str) -> str:
    # bcrypt works with bytes
    prehashed = _prehash(password).encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(prehashed, salt).decode("utf-8")

# Hash the new password
hashed_password = hash_password(new_password)

# Update Firestore
user_ref.update({
    "app_password_hash": hashed_password,
    "created_by_admin": True
})

print(f"Password updated successfully to: {new_password}")