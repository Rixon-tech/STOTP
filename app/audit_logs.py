from datetime import datetime
from google.cloud import firestore
from app.firestore_db import db

def log_event(google_id: str, username: str, event: str):
    # 1. Log the immutable event
    db.collection("auth_logs").add({
        "google_id": google_id,
        "username": username,
        "event": event,
        "timestamp": datetime.utcnow()
    })

    # 2. Update the user's state fields
    update_data = {}
    if event == "login":
        update_data = {
            "last_login": firestore.SERVER_TIMESTAMP,
            "is_active_session": True
        }
    elif event == "logout":
        update_data = {
            "last_logout": firestore.SERVER_TIMESTAMP,
            "is_active_session": False
        }

    if update_data:
        try:
            db.collection("users").document(google_id).update(update_data)
        except Exception as e:
            print(f"Warning: Could not update user timestamp: {e}")

def get_auth_logs(google_id: str = None):
    """Retrieves recent auth logs. If google_id is None, returns all logs."""
    logs_ref = db.collection("auth_logs")
    
    if google_id:
        # FETCH WITHOUT ORDER_BY to avoid "Missing Index" 500 errors
        query = logs_ref.where("google_id", "==", google_id).limit(50).get()
    else:
        # Single field order_by works fine out of the box
        query = logs_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(100).get()
    
    logs = [
        {
            "event": doc.get("event"),
            "timestamp": doc.get("timestamp").isoformat() if doc.get("timestamp") and hasattr(doc.get("timestamp"), "isoformat") else str(doc.get("timestamp")),
            "username": doc.get("username")
        }
        for doc in query
    ]

    # Sort in memory for user-specific logs
    if google_id:
        logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return logs