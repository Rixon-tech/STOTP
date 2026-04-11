from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from app.auth_google import verify_google_token
from app.auth_password import verify_admin_password, verify_manager_login
from app.auth_otp import verify_user_otp, get_otp_secret, generate_qr_code
from app.audit_logs import log_event, get_auth_logs
from app.export_logs import generate_logs_excel, generate_logs_csv
from app.notifier import send_security_alert
from app.firestore_db import db

import os
import hmac
import hashlib
import time
import requests
from dotenv import load_dotenv

load_dotenv()   

# ==============================
# CONFIG
# ==============================
DEVICE_SECRET = os.getenv('DEVICE_SECRET').encode()
ESP_URL = os.getenv('ESP_URL')

app = FastAPI()

# ==============================
# CORS CONFIGURATION
# ==============================
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with your Firebase URL like: ["https://stotp-xxxx.web.app"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount frontend directory to serve images/assets
app.mount("/assets", StaticFiles(directory="frontend"), name="assets")

# ==============================
# ESP COMMAND SENDER
# ==============================
def send_esp_command(cmd: str, username: str):
    username = username or ""
    ts = str(int(time.time()))
    payload = f"{cmd}:{username}:{ts}"

    sig = hmac.new(
        DEVICE_SECRET,
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    data = {
        "cmd": cmd,
        "user": username,
        "ts": ts,
        "sig": sig
    }
    print('ESP Command: ', data)
    
    try:
        if ESP_URL:
            requests.post(ESP_URL, json=data, timeout=3)
    except Exception as e:
        print(f"ESP Connection Error: {e}")
        # ESP offline should NOT block auth
        pass

# ==============================
# HEARTBEAT TASK
# ==============================
import threading

def start_heartbeat():
    def heartbeat_loop():
        while True:
            try:
                send_esp_command("HEARTBEAT", "SERVER")
            except:
                pass
            time.sleep(5)
    
    thread = threading.Thread(target=heartbeat_loop, daemon=True)
    thread.start()

@app.on_event("startup")
async def startup_event():
    start_heartbeat()


# ==============================
# FRONTEND
# ==============================
@app.get("/", response_class=HTMLResponse)
def serve_ui():
    # Use utf-8 encoding to support special characters in login.html
    with open("frontend/index.html", encoding="utf-8") as f:
        return f.read()


# ==============================
# GOOGLE TOKEN VERIFY
# ==============================
@app.post("/verify-token")
async def verify_token_endpoint(authorization: str = Header(None)):
    user = verify_google_token(authorization)
    # PRINT FOR REGISTRATION REFERENCE (User requirement)
    print(f"\n[GOOGLE_ID_REGISTER] Email: {user['email']} | Google ID: {user['sub']}\n")

    return {
        "email": user["email"],
        "sub": user["sub"],
        "role": user.get("role"),
        "exists": user.get("exists", False),
        "otp_enabled": user.get("otp_enabled", False)
    }

# ==============================
# ADMIN PASSWORD LOGIN
# ==============================
@app.post("/register-user")
async def register_user(authorization: str = Header(None), data: dict = None):
    user = verify_google_token(authorization)
    if user.get("exists"):
        raise HTTPException(400, "User already exists")
    
    from app.security import hash_password
    p_hash = hash_password(data["password"])
    username = user["email"].split("@")[0]
    db.collection("users").document(user["sub"]).set({
        "email": user["email"],
        "username": username,
        "app_password_hash": p_hash,
        "role": "user",
        "otp_enabled": False,
        "created_by_admin": True,
        "created_at": int(time.time())
    })
    
    return {"status": "registered", "username": username}

@app.post("/username-login")
async def username_login(authorization: str = Header(None), data: dict = None):
    user = verify_google_token(authorization)
    google_id = user["sub"]
    user_email = user.get("email", "unknown")

    try:
        user_data = verify_admin_password(google_id, data["password"])
        
        # ✅ Reset password failure count on success
        db.collection("users").document(google_id).update({
            "password_failures": 0
        })

        username = user_data.get("username", "unknown")
        log_event(google_id, username, "login")

        # 🔔 ESP LCD: Login Successful
        send_esp_command("LOGIN_SUCCESS", username)

        return {
            "otp_required": True,
            "otp_enabled": user_data.get("otp_enabled", False),
            "role": user_data.get("role", "user")
        }
    except HTTPException as e:
        if e.status_code == 401:
            # ❌ Password Incorrect: Increment Failure Counter
            user_ref = db.collection("users").document(google_id)
            doc = user_ref.get()
            data_dict = doc.to_dict() or {}
            failures = data_dict.get("password_failures", 0) + 1
            username = data_dict.get("username", "unknown")
            user_ref.update({"password_failures": failures})

            if failures >= 3:
                send_security_alert(user_email, username, "Password", failures)
        
        raise e


@app.post("/login-manager")
async def login_manager_endpoint(data: dict = None):
    """Direct login for managers using email and password."""
    user_data = verify_manager_login(data["email"], data["password"])
    
    # Prefix token so verify_google_token knows to handle it directly
    mock_token = f"MANAGER_{user_data['sub']}"
    
    return {
        "status": "success",
        "token": mock_token,
        "email": user_data.get("email", "manager"),
        "role": "manager",
        "otp_required": False,
        "otp_enabled": False
    }


# ==============================
# OTP SETUP
# ==============================
@app.get("/setup-otp")
def setup_otp(authorization: str = Header(None)):
    user = verify_google_token(authorization)
    # Use auto_create=True only here
    secret = get_otp_secret(user["sub"], auto_create=True, email=user["email"])
    qr_b64 = generate_qr_code(user["email"], secret)
    return {"qr_code": qr_b64}


# ==============================
# OTP VERIFICATION
# ==============================
@app.post("/verify-otp")
def verify_otp(authorization: str = Header(None), data: dict = None):
    user = verify_google_token(authorization)
    google_id = user["sub"]
    user_email = user.get("email", "unknown")
    
    send_esp_command("VERIFYING_OTP", user_email)

    if not verify_user_otp(google_id, data["otp"]):
        # ❌ OTP Incorrect: Increment Failure Counter
        user_ref = db.collection("users").document(google_id)
        doc = user_ref.get()
        data_dict = doc.to_dict() or {}
        failures = data_dict.get("otp_failures", 0) + 1
        username = data_dict.get("username", "unknown")
        user_ref.update({"otp_failures": failures})

        if failures >= 3:
            send_security_alert(user_email, username, "OTP", failures)

        # ❌ ESP LCD: Access Denied
        send_esp_command("OTP_DENIED", user_email)
        raise HTTPException(401, "Invalid OTP")

    # ✅ Reset OTP failure count on success
    db.collection("users").document(google_id).update({
        "otp_failures": 0
    })

    # ✅ ESP LCD + Servo: Access Granted
    send_esp_command("OTP_GRANTED", user_email)

    return {"status": "authenticated"}


# ==============================
# LOGOUT
# ==============================
@app.post("/logout")
async def logout(authorization: str = Header(None)):
    user = verify_google_token(authorization)

    log_event(user["sub"], user.get("email"), "logout")

    # 🔒 ESP LCD: Locked
    send_esp_command("LOGOUT", user.get("email", "user"))

    return {"status": "logged_out"}


@app.get("/user-logs")
def user_logs_endpoint(authorization: str = Header(None)):
    user = verify_google_token(authorization)
    google_id = user["sub"]
    
    # If Manager, see ALL logs. If User, see only OWN logs.
    if user.get("role") == "manager":
        logs = get_auth_logs(None)
    else:
        logs = get_auth_logs(google_id)
        
    return {"logs": logs}


# ==============================
# DOWNLOAD LOGS
# ==============================
@app.get("/download-logs")
def download_logs(authorization: str = Header(None)):
    user = verify_google_token(authorization)
    
    if user.get("role") != "manager":
        raise HTTPException(403, "Access restricted to managers")

    # Generate CSV for the entire system
    csv_file = generate_logs_csv(None)
    if not csv_file:
        raise HTTPException(404, "No logs available to export")

    return StreamingResponse(
        csv_file,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=system_audit_logs.csv"}
    )

@app.get("/view-document")
def view_document():
    import os
    pdf_path = "CONFERENCE PAPER FOR FINAL YR PROJECT.pdf"
    if not os.path.exists(pdf_path):
        raise HTTPException(404, "Document not found")
        
    return FileResponse(
        pdf_path, 
        media_type="application/pdf"
    )