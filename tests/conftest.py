from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from webapp.database import Base
from webapp.models import Role, User
from webapp.security import hash_password


@pytest.fixture()
def db_session(tmp_path) -> Session:
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, future=True)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)

    session = TestingSession()
    try:
        role = Role(name="admin")
        session.add(role)
        session.commit()
        session.refresh(role)

        user = User(
            username="admin",
            password_hash=hash_password("admin"),
            role_id=role.id,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        session.add(user)
        session.commit()
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
