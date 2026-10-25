.PHONY: build up down logs shell test clean

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

shell-backend:
	docker-compose exec backend /bin/bash

shell-frontend:
	docker-compose exec frontend /bin/sh

test:
	docker-compose exec backend pytest

clean:
	docker-compose down -v
	docker system prune -f

demo-data:
	cd synthetic_data && python generate_scenario.py

reset-db:
	docker-compose down -v
	docker-compose up -d postgres neo4j qdrant
	sleep 5
	docker-compose up -d
