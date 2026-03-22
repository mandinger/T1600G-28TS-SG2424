from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    repo_root: Path
    data_dir: Path
    encryption_key: str
    bootstrap_admin_username: str
    bootstrap_admin_password: str
    session_ttl_hours: int
    tftp_ip: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    repo_root = Path(__file__).resolve().parents[1]
    data_dir = Path(os.getenv("APP_DATA_DIR", str(repo_root / "data"))).expanduser().resolve()
    return Settings(
        repo_root=repo_root,
        data_dir=data_dir,
        encryption_key=os.getenv("APP_ENCRYPTION_KEY", "change-this-key"),
        bootstrap_admin_username=os.getenv("APP_BOOTSTRAP_ADMIN_USERNAME", "admin"),
        bootstrap_admin_password=os.getenv("APP_BOOTSTRAP_ADMIN_PASSWORD", "admin"),
        session_ttl_hours=int(os.getenv("APP_SESSION_TTL_HOURS", "12")),
        tftp_ip=os.getenv("APP_TFTP_IP", "").strip(),
    )
