# Repository Guidelines

## Project Structure & Module Organization
OpenHands couples a Python backend with a Vite/React frontend. Key directories:
- `openhands/` – FastAPI services, runtime integrations, CLI entrypoints.
- `frontend/` – TypeScript UI (`src/`), npm tooling, Playwright setup.
- `microagents/` – packaged agent behaviors imported by the backend.
- `tests/` – unit suites; broader flows live in `evaluation/integration_tests`.
- `docs/`, `scripts/`, `containers/` – documentation, automation helpers, dev environments.

## Build, Test, and Development Commands
Run `make build` once to install Poetry, npm packages, and pre-commit hooks. `make run` boots both servers; use `make start-backend` or `make start-frontend` when focusing on one tier. Configure models with `make setup-config`; prefer `poetry add <package>` when adjusting dependencies.

## Coding Style & Naming Conventions
Python code targets 3.12, four-space indentation, snake_case files, and type hints where available. Pre-commit runs Ruff, mypy, and formatting—trigger it with `poetry run pre-commit run --all-files` before committing. Frontend code follows the repo’s ESLint/Prettier rules via `npm run lint`; keep PascalCase React components and camelCase utilities.

## Testing Guidelines
Add pytest modules named `test_<feature>.py` under `tests/unit` and execute them with `poetry run pytest`. Reserve `evaluation/integration_tests` for cross-service scenarios and coordinate when expanding that harness. UI work should include `npm run test` (and Playwright specs when behavior changes); mention executed suites in your PR description.

## Commit & Pull Request Guidelines
Use conventional prefixes already present in the history (`feat`, `fix`, `docs`, `test`, etc.) and keep subject lines under 72 characters. Bundle logical changes per commit, updating docs or tests alongside code. PRs should summarize intent, list validation steps (`make lint`, `poetry run pytest`, `npm run test`), link related issues, and attach screenshots or transcripts for UI or CLI changes.

## Configuration & Security Notes
Start from `config.template.toml` and run `make setup-config` to create a local `config.toml`; keep credentials out of version control. For runtime experiments, set overrides like `SANDBOX_RUNTIME_CONTAINER_IMAGE` via environment variables instead of editing tracked files.
