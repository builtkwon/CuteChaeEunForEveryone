import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_CLIENT_ID     = os.environ["GOOGLE_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_CLIENT_SECRET"]
SECRET_KEY           = os.environ.get("SECRET_KEY", "change-this-in-production")
BASE_URL             = os.environ.get("BASE_URL", "http://localhost:8000")

DRIVE_FOLDER_NAME = "PhotoFrame"
QR_POSITION       = "bottom-right"   # top-left / top-right / bottom-left / bottom-right
QR_SIZE_RATIO     = 0.15             # 사진 짧은 변의 15%
QR_MARGIN         = 20               # 가장자리 여백 (px)
