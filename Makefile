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

run-upload:
	python -m app.main upload data/images/cat_001.jpg

run-query:
	python -m app.main query cat --seed-images data/images/cat_001.jpg data/images/dog_001.jpg