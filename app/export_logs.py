import pandas as pd
from google.cloud import firestore
import io
from app.firestore_db import db

def generate_logs_dataframe(google_id: str = None):
    # 1. Fetch logs from Firestore
    query = db.collection("auth_logs")
    if google_id:
        query = query.where(filter=firestore.FieldFilter("google_id", "==", google_id))
    
    docs = query.stream()

    logs_data = []
    for doc in docs:
        data = doc.to_dict()
        if "timestamp" in data and data["timestamp"] and hasattr(data["timestamp"], "isoformat"):
            data["timestamp"] = data["timestamp"].isoformat()
        logs_data.append(data)
    
    # Sort and create DF
    logs_data.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    if not logs_data: return None
    return pd.DataFrame(logs_data)

def generate_logs_excel(google_id: str = None):
    df = generate_logs_dataframe(google_id)
    if df is None: return None
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Logs')
    output.seek(0)
    return output

def generate_logs_csv(google_id: str = None):
    df = generate_logs_dataframe(google_id)
    if df is None: return None
    output = io.BytesIO()
    # Save as CSV with utf-8-sig (for Excel compatibility)
    output.write(df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8'))
    output.seek(0)
    return output