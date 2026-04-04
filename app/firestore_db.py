from google.cloud import firestore
from google.oauth2 import service_account
from app.config import SERVICE_ACCOUNT_FILE

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE
)

db = firestore.Client(credentials=credentials)
