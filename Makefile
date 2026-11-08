.PHONY: install test lint run up down k8s-apply k8s-delete

install:
	pip install -r requirements-dev.txt

test:
	pytest -q

lint:
	ruff check app tests

run:
	DB_PATH=./local.db uvicorn app.main:app --reload

up:
	docker compose up -d --build

down:
	docker compose down

k8s-apply:
	kubectl apply -f k8s/namespace.yaml
	kubectl apply -f k8s/

k8s-delete:
	kubectl delete namespace taskboard
