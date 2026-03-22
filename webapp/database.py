from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import get_settings

settings = get_settings()

Path(settings.data_dir).mkdir(parents=True, exist_ok=True)

database_url = f"sqlite:///{settings.data_dir / 'app.db'}"
engine = create_engine(database_url, connect_args={"check_same_thread": False}, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()
