install:
	pip install -r requirements.txt

test:
	pytest -q

test-cov:
	pytest --cov=app --cov-report=term-missing

lint:
	ruff check .

redis-up:
	docker compose up -d

redis-down:
	docker compose down