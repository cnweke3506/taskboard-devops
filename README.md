# TaskBoard DevOps

A small task-tracking API, built to practice the full DevOps lifecycle: code → tests → container → CI/CD → cloud infrastructure → Kubernetes → monitoring.

The app itself is intentionally simple. The point of this repo is everything around it.

## Architecture

```
 Developer ──git push──▶ GitHub ──▶ GitHub Actions
                                     ├─ lint (ruff) + test (pytest)
                                     └─ build image ──▶ GitHub Container Registry (ghcr.io)
                                                              │
                     ┌────────────────────────────────────────┴───────────────┐
                     ▼                                                        ▼
        AWS (provisioned by Terraform)                             Kubernetes (minikube / EKS)
        VPC ─ public subnet ─ security group                       Deployment + Service + PVC
        EC2 (Amazon Linux) running the container                   readiness/liveness probes
                     │                                                        │
                     └──────────── /health and /metrics ──▶ Prometheus ──▶ Grafana
```

## Tech stack

| Area | Tools |
| --- | --- |
| App | Python, FastAPI, SQLite |
| Testing / lint | pytest, ruff |
| Containers | Docker (multi-stage, non-root), Docker Compose |
| CI/CD | GitHub Actions → GitHub Container Registry |
| Infrastructure as Code | Terraform (VPC, subnet, internet gateway, security group, EC2) |
| Orchestration | Kubernetes (Deployment, Service, ConfigMap, PersistentVolumeClaim) |
| Observability | Prometheus metrics, Grafana, structured JSON logs, health checks |

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Health check (used by Docker, Kubernetes, monitoring) |
| GET | `/metrics` | Prometheus metrics (request count, latency) |
| GET | `/tasks` | List tasks |
| POST | `/tasks` | Create a task `{"title": "..."}` |
| PATCH | `/tasks/{id}/done` | Mark a task done |
| DELETE | `/tasks/{id}` | Delete a task |

Interactive docs: `http://localhost:8000/docs`

## Run it

### 1. Locally (Python)
```bash
python -m venv venv
venv\Scripts\activate          # Windows PowerShell
# source venv/bin/activate     # Mac/Linux
pip install -r requirements-dev.txt
pytest -q
uvicorn app.main:app --reload  # set DB_PATH=./local.db first on Windows: $env:DB_PATH="./local.db"
```

### 2. With Docker Compose (app + Prometheus + Grafana)
```bash
docker compose up -d --build
```
- App: http://localhost:8000/docs
- Prometheus: http://localhost:9090 (try the query `http_requests_total`)
- Grafana: http://localhost:3000 (admin / admin), add Prometheus data source `http://prometheus:9090`

### 3. On Kubernetes (minikube)
```bash
minikube start
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/
kubectl -n taskboard get pods
kubectl -n taskboard port-forward svc/taskboard 8080:80
```
Update the image in `k8s/deployment.yaml` to your GHCR image first.

### 4. On AWS with Terraform
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars   # fill in your IP, key pair, image
terraform init
terraform plan
terraform apply
# open the app_url output, then when finished:
terraform destroy
```

## Cost safety
- Set an **AWS billing alarm** before running Terraform.
- The design avoids NAT gateways and load balancers, which are not free-tier.
- Always run `terraform destroy` when you finish a session.

## What I'd do next
- Move from SQLite to PostgreSQL (Amazon RDS) so the app can scale past one replica.
- Deploy to Amazon EKS and add an Ingress with TLS.
- Store Terraform state remotely in S3 with locking.
- Add alerting rules (error rate, latency) and a CD step that deploys automatically.

See `docs/RUNBOOK.md` for troubleshooting and incident steps.

Local dev environment: WSL2 Ubuntu + Docker Desktop (verified Nov 2026).
