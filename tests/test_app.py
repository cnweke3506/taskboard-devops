import os
import tempfile

os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def client():
    return TestClient(app)


def test_health():
    with client() as c:
        r = c.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


def test_task_lifecycle():
    with client() as c:
        r = c.post("/tasks", json={"title": "Write runbook"})
        assert r.status_code == 201
        task_id = r.json()["id"]
        assert any(t["id"] == task_id for t in c.get("/tasks").json())
        assert c.patch(f"/tasks/{task_id}/done").json()["done"] is True
        assert c.delete(f"/tasks/{task_id}").status_code == 204
        assert c.delete(f"/tasks/{task_id}").status_code == 404


def test_validation():
    with client() as c:
        assert c.post("/tasks", json={"title": ""}).status_code == 422


def test_metrics_exposed():
    with client() as c:
        c.get("/health")
        body = c.get("/metrics").text
        assert "http_requests_total" in body
