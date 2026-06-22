# Contributing to SystemForge AI

Thanks for helping improve SystemForge AI. This guide keeps contributions easy to review, reproduce, and merge.

## 1. Find a contribution

- Start with [Good First Issues](docs/GOOD_FIRST_ISSUES.md).
- Check the GitHub issue templates before opening a new report.
- For architectural changes, open an issue or ADR proposal before a large implementation.

## 2. Branch and PR flow

- Do not commit directly to `main` or `master`.
- Use a focused branch:
  - `feat/<short-topic>`
  - `fix/<short-topic>`
  - `docs/<short-topic>`
- Complete the pull request template, including what changed, why, and how it was tested.

## 3. Development setup

```bash
cp .env.example .env
docker compose up --build
```

Local backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

Local frontend:

```bash
cd frontend
npm ci
npm run dev
```

## 4. Required quality checks

Run before opening a pull request:

```bash
ruff check backend/app backend/tests
mypy backend/app backend/tests
pytest backend/tests -q

cd frontend
npm run lint
npx tsc --noEmit
npm run test
npm run build
```

For user-visible flows, also run:

```bash
cd frontend
npm run test:e2e
```

## 5. Code style and scope

- Keep changes small and focused.
- Do not mix unrelated refactors or formatting into the same pull request.
- Update API docs and tests when a contract changes.
- Add an Alembic migration for every schema change.
- Preserve workspace isolation and authorization checks in every data path.

## 6. Security and secrets

- Never commit secrets, credentials, or local `.env` values.
- Follow [SECURITY.md](SECURITY.md) for private vulnerability reports.
- Add regression tests for security fixes when disclosure timing allows.

## 7. Commit messages

- `feat: add workspace budget alert endpoint`
- `fix: prevent stale websocket reconnect loop`
- `docs: expand production hardening checklist`

Conventional commit prefixes drive semantic release automation.

## 8. Documentation expectations

Update documentation when you add an endpoint, service, worker, environment variable, migration step, or user-visible behavior.

Release-impacting changes should update:

- `README.md` when setup or product behavior changes.
- The relevant file under `docs/` or `ops/`.
- `CHANGELOG.md`.

Maintainers should also follow [docs/MAINTAINER_GUIDE.md](docs/MAINTAINER_GUIDE.md).
