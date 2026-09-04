from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select


TEST_DATABASE = Path(tempfile.gettempdir()) / f"teamflow-pytest-{os.getpid()}.sqlite3"
if TEST_DATABASE.exists():
    TEST_DATABASE.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DATABASE}"
os.environ["SEED_DEMO"] = "false"

from app.db.session import SessionLocal
from app.domain.models import User, Workspace
from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def created_users():
    user_ids: list[int] = []
    yield user_ids
    db = SessionLocal()
    try:
        if user_ids:
            owned_workspaces = db.scalars(select(Workspace).where(Workspace.owner_id.in_(user_ids))).all()
            for workspace in owned_workspaces:
                db.delete(workspace)
            db.flush()
            db.execute(delete(User).where(User.id.in_(user_ids)))
            db.commit()
    finally:
        db.close()
