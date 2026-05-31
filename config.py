import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_CLIENT_ID     = os.environ["GOOGLE_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_CLIENT_SECRET"]
SECRET_KEY           = os.environ.get("SECRET_KEY", "change-this-in-production")
BASE_URL             = os.environ.get("BASE_URL", "http://localhost:8000")

DRIVE_FOLDER_NAME = "PhotoFrame"
