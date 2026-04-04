import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
ALERT_EMAIL = os.getenv("ALERT_EMAIL")

def send_security_alert(user_email: str, username: str, attempt_type: str, attempts: int):
    """Sends a security alert email when multiple failed attempts are detected."""
    if not all([SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASS, ALERT_EMAIL]):
        print(f"WARNING: SMTP configuration is incomplete. Skip sending alert for {username} ({user_email}).")
        return

    subject = f"⚠️ SECURITY WARNING: Multiple Failed Login Attempts for User: {username}"
    body = f"""
    IMPORTANT SECURITY WARNING
    
    The security system has detected suspicious login activity for the following account:
    - Username: {username}
    - Email: {user_email}
    
    Alert Details:
    - Attempt Type: {attempt_type} (Incorrect credentials)
    - Total Failed Attempts: {attempts}
    
    WARNING: Someone is repeatedly trying to access this account with incorrect credentials. 
    This could be a replay attack or a brute-force attempt.
    
    Action Required:
    1. Please investigate this activity immediately.
    2. Consider blocking the IP or resetting the user's password if the activity continues.
    """

    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = ALERT_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(SMTP_SERVER, int(SMTP_PORT)) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
            print(f"Security alert email sent to {ALERT_EMAIL} for user {user_email}.")
    except Exception as e:
        print(f"ERROR: Failed to send security alert email: {e}")
