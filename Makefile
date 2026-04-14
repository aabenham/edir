install:
	pip install -r requirements.txt

test:
	pytest -q

test-unit:
	pytest tests/unit -q

test-integration:
	pytest tests/integration -q

test-cov:
	pytest --cov=app --cov-report=term-missing

lint:
	ruff check .

redis-up:
	docker compose up -d

redis-down:
	docker compose down