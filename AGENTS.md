# Repository Guidelines

## Project Structure & Module Organization
- `python/src/hack/rest_server`: FastAPI entrypoints, providers, and exception handlers.
- `python/src/hack/core`: Domain services and shared models.
- `python/src/hack/integration_tests`: Pytest suites exercising the running stack.
- `python/alembic.ini` and `python/alembic-entrypoint.sh`: Migration config and entrypoint used in containers.
- Root `compose.yaml`/`compose.override.yaml*`: Docker Compose stack (Postgres, Redis, REST API); `Makefile` wraps common workflows; copy `./.env.example` and `./python/.env.example` before running anything.

## Build, Test, and Development Commands
- `make up`: Build images, start the stack, and run migrations.
- `make run-migrations`: Apply Alembic migrations against the running Postgres.
- `make generate-migrations m="001" msg="add users"`: Create an autogeneration revision (runs inside the Alembic tool container).
- `make test` or `docker compose run --rm --build run-integration-tests`: Run integration tests inside the test container.
- `docker compose logs -f`: Stream container logs for debugging.

## Coding Style & Naming Conventions
- Python 3.12; 4-space indentation; keep lines ≤79 chars (enforced by `ruff`).
- Ruff checks `E,F,UP,B,SIM,I`; fix or silence findings intentionally.
- Use type hints and dataclasses/Pydantic models where applicable; prefer explicit imports over wildcards.
- Modules and files use `snake_case`; tests follow `test_*.py` and function names describe behavior.

## Testing Guidelines
- Tests live in `python/src/hack/integration_tests`; fixtures reside in `conftest.py`.
- Target new endpoints/services with `test_*.py` cases; prefer deterministic data setup over relying on existing state.
- Run `make test` before pushing; to scope locally, use `docker compose run --rm run-integration-tests -k "<pattern>"`.
- If migrations change schema, add/adjust tests that cover the new behavior and ensure they pass in the containerized environment.

## Commit & Pull Request Guidelines
- Write imperative, focused commit messages (e.g., `Add appeal routing tests`, `Fix login session provider`); group related changes with their migrations.
- PRs should include: summary of changes, local/test commands run, and any config or env updates required. Add screenshots or sample requests/responses when REST behavior changes.
- Keep branches small and reviewable; avoid mixing refactors with functional changes unless tightly coupled.

## Security & Configuration Tips
- Never commit `.env` files or secrets; use the provided `.env.example` templates.
- The stack expects Postgres and Redis from Compose; use the provided host/port defaults unless you know the impact.
- Run migrations only after the database container is healthy to avoid partial state.
