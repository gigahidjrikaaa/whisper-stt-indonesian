# Repository Guidelines

## Project Structure & Module Organization
- app/core: configuration, logging, exceptions (e.g., `app/core/config.py`).
- app/models: model manager and schemas (`whisper.py`, `schemas.py`).
- app/services: business logic (`transcription.py`).
- app/routers: FastAPI routes (`transcription.py`).
- main.py: FastAPI entrypoint. Tests live in `test_api.py`, `test_server.py`. Logs in `logs/`.

Example layout:
```
app/{core,models,services,routers}/
main.py  requirements.txt  Dockerfile  docker-compose.yml
```

## Build, Test, and Development Commands
- Install: `pip install -r requirements.txt`
- Dev server: `fastapi dev main.py`
- Prod server: `fastapi run main.py --host 0.0.0.0 --port 8000`
- Helper script: `./run.sh dev` (dev) or `./run.sh` (prod)
- Docker: `docker-compose up -d` (exposes `http://localhost:8000`)
- Tests: `pytest -v`

## Coding Style & Naming Conventions
- Python 3.8+, follow PEP 8 with 4‑space indentation and type hints.
- Files/modules: snake_case; classes: PascalCase; functions/vars: snake_case; constants: UPPER_CASE.
- Routers under `app/routers`, services under `app/services`, config/logging under `app/core`.
- Pydantic schemas in `app/models/schemas.py`. Keep concise docstrings and informative logging via `app/core/logging.py`.

## Testing Guidelines
- Framework: pytest. Name files `test_*.py` (examples: `test_api.py`, `test_server.py`).
- Run all tests: `pytest -v`. Filter: `pytest -k transcribe`.
- Add tests for new endpoints/services; prefer API-level tests using `fastapi.testclient`.
- Keep tests fast and deterministic; avoid loading large models unless essential.

## Commit & Pull Request Guidelines
- Commits: follow Conventional Commits (e.g., `feat(routers): add /api/v1/transcribe validation`).
- PRs should include:
  - Clear summary, linked issues (e.g., `Fixes #123`).
  - What changed and why, plus test plan (commands/cURL samples).
  - Any API or config changes; update `README.md` if applicable.
  - Screenshots or logs when relevant (e.g., health check output).

## Security & Configuration Tips
- Use `.env` (see `.env.example`) for `MODEL_SIZE`, `DEVICE`, `COMPUTE_TYPE`, `LOG_LEVEL`.
- GPU: ensure CUDA libs available; in Docker this is handled. CPU fallback: set `DEVICE=cpu`.
- Do not commit secrets or large audio assets. Keep uploads under `MAX_FILE_SIZE_MB`.

