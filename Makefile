.PHONY: dev-up dev-down test-up test-down clean test

dev-up:
	docker-compose up -d
	poetry run python scripts/setup/check_health.py
	poetry run alembic upgrade head

dev-down:
	docker-compose down

test-up:
	docker-compose -f docker-compose.test.yml up -d
	sleep 5
	poetry run alembic -x config=test upgrade head

test-down:
	docker-compose -f docker-compose.test.yml down -v

clean:
	docker-compose down -v
	docker-compose -f docker-compose.test.yml down -v
	rm -rf timescale_data/

test: test-up
	poetry run pytest tests/integration -v
	$(MAKE) test-down
