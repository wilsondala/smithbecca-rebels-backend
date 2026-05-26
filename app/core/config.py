import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH, override=False, encoding="utf-8")

DATABASE_URL = (os.getenv("DATABASE_URL") or "").strip().strip('"').strip("'")
SECRET_KEY = (os.getenv("SECRET_KEY") or "").strip().strip('"').strip("'")
ALGORITHM = (os.getenv("ALGORITHM") or "HS256").strip().strip('"').strip("'")

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    (os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES") or "60")
    .strip()
    .strip('"')
    .strip("'")
)

# ===============================
# GOOGLE AUTH
# ===============================
GOOGLE_CLIENT_ID = (os.getenv("GOOGLE_CLIENT_ID") or "").strip().strip('"').strip("'")

# ===============================
# FACEBOOK AUTH (FIX DO ERRO)
# ===============================
FACEBOOK_APP_ID = (os.getenv("FACEBOOK_APP_ID") or "").strip().strip('"').strip("'")
FACEBOOK_APP_SECRET = (os.getenv("FACEBOOK_APP_SECRET") or "").strip().strip('"').strip("'")