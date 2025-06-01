COMPOSE_FILE=docker-compose.local.yml
SERVICE=django


upbuild: build up
up:
	docker compose -f $(COMPOSE_FILE) up

build:
	docker compose -f $(COMPOSE_FILE) build

run:
	docker compose -f $(COMPOSE_FILE) run --rm $(filter-out $@,$(MAKECMDGOALS))

restart:
	docker compose -f $(COMPOSE_FILE) restart $(filter-out $@,$(MAKECMDGOALS))

shell:
	docker compose -f $(COMPOSE_FILE) exec $(SERVICE) python manage.py shell_plus

bash:
	docker compose -f $(COMPOSE_FILE) exec $(SERVICE) bash

down:
	docker compose -f $(COMPOSE_FILE) down

destroy:
	docker compose -f $(COMPOSE_FILE) down -v

createsuperuser:
	docker compose -f $(COMPOSE_FILE) exec $(SERVICE) python manage.py createsuperuser

makemigrations:
	docker compose -f $(COMPOSE_FILE) run --rm $(SERVICE) python manage.py makemigrations $(filter-out $@,$(MAKECMDGOALS))

migrate:
	docker compose -f $(COMPOSE_FILE) run --rm $(SERVICE) python manage.py migrate $(filter-out $@,$(MAKECMDGOALS))

urls:
	docker compose -f $(COMPOSE_FILE) run --rm $(SERVICE) python manage.py show_urls

logs:
	docker compose -f $(COMPOSE_FILE) logs -f $(filter-out $@,$(MAKECMDGOALS))

test:
	docker compose -f $(COMPOSE_FILE) run --rm $(SERVICE) pytest

test_local:
	docker compose -f $(COMPOSE_FILE) exec $(SERVICE) python manage.py test --settings=config.settings.test $(filter-out $@,$(MAKECMDGOALS))

rm_pyc:
	find . -name "__pycache__" -o -name "*.pyc" | xargs rm -rf

stagingup:
	docker compose -f staging.yml up -d --build
