import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-in-production")

R2_ACCOUNT_ID        = os.environ["R2_ACCOUNT_ID"]
R2_ACCESS_KEY_ID     = os.environ["R2_ACCESS_KEY_ID"]
R2_SECRET_ACCESS_KEY = os.environ["R2_SECRET_ACCESS_KEY"]
R2_BUCKET_NAME       = os.environ["R2_BUCKET_NAME"]
R2_PUBLIC_URL        = os.environ["R2_PUBLIC_URL"]  # 예: https://pub-xxxx.r2.dev

DRIVE_FOLDER_NAME = "PhotoFrame"  # 하위 호환용, 추후 제거 가능
