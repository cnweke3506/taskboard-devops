"""TaskBoard API: a small service used to practice DevOps end to end."""
import logging
import os
import sqlite3
import time
from contextlib import contextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import BaseModel, Field

DB_PATH = os.getenv("DB_PATH", "/data/tasks.db")
APP_VERSION = os.getenv("APP_VERSION", "dev")

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}',
)
log = logging.getLogger("taskboard")

REQUESTS = Counter("http_requests_total", "HTTP requests", ["method", "path", "status"])
LATENCY = Histogram("http_request_duration_seconds", "Request latency", ["path"])

app = FastAPI(title="TaskBoard API", version=APP_VERSION)


@contextmanager
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    with db() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS tasks ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0)"
        )


@app.on_event("startup")
def startup():
    init_db()
    log.info(f"TaskBoard {APP_VERSION} started, db={DB_PATH}")


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    path = request.url.path
    LATENCY.labels(path).observe(time.perf_counter() - start)
    REQUESTS.labels(request.method, path, response.status_code).inc()
    return response


class TaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class Task(TaskIn):
    id: int
    done: bool


@app.get("/health")
def health():
    """Liveness/readiness check used by Docker, Kubernetes, and monitoring."""
    try:
        with db() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok", "version": APP_VERSION}
    except sqlite3.Error as e:
        log.error(f"health check failed: {e}")
        raise HTTPException(status_code=503, detail="database unavailable")


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/tasks", response_model=list[Task])
def list_tasks():
    with db() as conn:
        rows = conn.execute("SELECT id, title, done FROM tasks ORDER BY id").fetchall()
    return [Task(id=r["id"], title=r["title"], done=bool(r["done"])) for r in rows]


@app.post("/tasks", response_model=Task, status_code=201)
def create_task(task: TaskIn):
    with db() as conn:
        cur = conn.execute("INSERT INTO tasks (title) VALUES (?)", (task.title,))
        task_id = cur.lastrowid
    log.info(f"created task {task_id}")
    return Task(id=task_id, title=task.title, done=False)


@app.patch("/tasks/{task_id}/done", response_model=Task)
def complete_task(task_id: int):
    with db() as conn:
        cur = conn.execute("UPDATE tasks SET done = 1 WHERE id = ?", (task_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="task not found")
        row = conn.execute("SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return Task(id=row["id"], title=row["title"], done=bool(row["done"]))


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    with db() as conn:
        cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="task not found")
    return Response(status_code=204)
