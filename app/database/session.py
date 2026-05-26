import os
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH, override=False, encoding="utf-8")

DATABASE_URL = (os.getenv("DATABASE_URL") or "").strip().strip('"').strip("'")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL não configurada.")

print("DATABASE_URL carregada:", repr(DATABASE_URL))

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"sslmode": "require"} if "localhost" not in DATABASE_URL and "127.0.0.1" not in DATABASE_URL else {},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()