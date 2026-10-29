from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import ingest
from app.core.database import get_db
from app.core.security import get_current_active_user


class FakeQuery:
    def __init__(self, project):
        self.project = project

    def filter(self, *conditions):
        return self

    def first(self):
        return self.project


class FakeDB:
    def __init__(self, project):
        self.project = project
        self.added = []
        self.committed = False

    def query(self, model):
        return FakeQuery(self.project)

    def add(self, value):
        self.added.append(value)

    def commit(self):
        self.committed = True

    def refresh(self, value):
        value.id = 42
        value.created_at = datetime(2026, 1, 1)


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    project = SimpleNamespace(id=7, user_id=11, status=None)
    db = FakeDB(project)
    user = SimpleNamespace(id=11, username="tester")
    app = FastAPI()
    app.include_router(ingest.router, prefix="/api/v1/projects")
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_active_user] = lambda: user
    monkeypatch.setattr(ingest.settings, "UPLOAD_DIR", str(tmp_path))
    async def no_op_process_file(*args, **kwargs):
        return None
    monkeypatch.setattr(ingest, "process_file", no_op_process_file)
    return TestClient(app), db, project, tmp_path


def test_ingest_rejects_unsupported_extension_before_saving(api_client):
    client, db, _, upload_dir = api_client
    response = client.post(
        "/api/v1/projects/7/ingest",
        files={"file": ("payload.exe", b"not an allowed type", "application/octet-stream")},
    )
    assert response.status_code == 415
    assert response.json()["detail"] == "Unsupported file type"
    assert not list(Path(upload_dir).iterdir())
    assert db.added == []


def test_ingest_rejects_project_not_owned_by_user(api_client):
    client, db, _, upload_dir = api_client
    db.project = None
    response = client.post(
        "/api/v1/projects/7/ingest",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"
    assert not list(Path(upload_dir).iterdir())


def test_ingest_saves_supported_file_with_safe_unique_name(api_client):
    client, db, project, upload_dir = api_client
    response = client.post(
        "/api/v1/projects/7/ingest",
        files={"file": (r"C:\\private\\notes.TXT", b"study notes", "text/plain")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == 42
    assert body["filename"] == "notes.TXT"
    assert body["ingestion_status"] == "pending"
    assert db.committed is True
    assert project.status.value == "ingesting"
    saved_files = list(Path(upload_dir).iterdir())
    assert len(saved_files) == 1
    assert saved_files[0].name.endswith(".txt")
    assert saved_files[0].name != "notes.TXT"
    assert saved_files[0].read_bytes() == b"study notes"
