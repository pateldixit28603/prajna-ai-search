.PHONY: install dev-api dev-web test build ingest-demo docker gpu

install:
	cd backend && python -m venv .venv && .venv/bin/pip install -r requirements.txt
	cd frontend && npm install

dev-api:
	cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

dev-web:
	cd frontend && npm run dev

test:
	cd backend && .venv/bin/pytest -q

build:
	cd frontend && npm run build

ingest-demo:
	cd backend && .venv/bin/python -m scripts.ingest wiki-titles "Nvidia" "CUDA" "Retrieval-augmented generation" "Large language model" "Bhagavad Gita"

docker:
	docker compose up --build

gpu:
	docker compose -f deploy/docker-compose.gpu.yml up --build
