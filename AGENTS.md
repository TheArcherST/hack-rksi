# Repository Guidelines

## Project Structure & Module Organization
- `python/src/hack/rest_server`: FastAPI entrypoints, providers, and exception handlers.
- `python/src/hack/core`: Domain services and shared models.
- `python/src/hack/integration_tests`: Pytest suites exercising the running stack.
- Endpoints implementation should be expressed in request handler, unless there some complex domain logic.
- Complex domain logic should be expressed as service and to be used by request handlers.

## Build, Test, and Development Commands
- `make up`: Build images, start the stack, and run migrations.
- `make run-migrations`: Apply Alembic migrations against the running Postgres.
- `make generate-migrations m="Add users"`: Create an autogeneration revision (runs inside the Alembic tool container).
- `make test`: Run integration tests inside the test container.
- `docker compose logs rest-server -f`: Stream container logs for debugging.

## Testing Guidelines
- Tests live in `python/src/hack/integration_tests`; fixtures reside in `conftest.py`.
- Target new endpoints/services with `test_*.py` cases; prefer deterministic data setup over relying on existing state.
- Run `make test` before pushing; to scope locally, use `make test args='-k "<pattern>"'`.
- If migrations change schema, add/adjust tests that cover the new behavior and ensure they pass in the containerized environment.

## Typical development cycle  (PLEASE JUST RUN COMMANDS, IT WILL WORK IN YOUR ENVIRONMENT)
1. Implement feature and tests
2. Run `make generate-migrations m="Migration message here"` to generate migrations if models alerted
3. Run `make up` to deploy locally + apply new migrations  
4. Run `make test` to run integration tests
5. Done
