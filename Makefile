# related with migrations
alembic:
	docker compose run --rm --build tool-alembic $(command)
run-migrations:
	make alembic command="upgrade head"
generate-migrations:
	make alembic command="revision -m '$(m) $(msg) $(message)' --autogenerate"

# related with end-user workflow
up:
	docker compose up --build -d && make run-migrations
test:
	docker compose run --rm --build run-integration-tests $(args)
update:
	git pull && make up && make test
logs:
	docker compose logs -f
down:
	docker compose down