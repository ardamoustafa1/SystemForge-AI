#!/usr/bin/env sh
set -eu

# Safe migration helper:
# - If DB already has tables but no alembic_version, stamp baseline first.
# - Then run upgrade head.

cd /app

TABLE_COUNT="$(python - <<'PY'
from sqlalchemy import create_engine, text
from app.core.config import get_settings

engine = create_engine(get_settings().database_url, future=True)
with engine.connect() as conn:
    count = conn.execute(
        text(
            "SELECT count(*) "
            "FROM information_schema.tables "
            "WHERE table_schema='public' "
            "AND table_name NOT IN ('alembic_version')"
        )
    ).scalar_one()
print(int(count))
PY
)"

HAS_ALEMBIC="$(python - <<'PY'
from sqlalchemy import create_engine, text
from app.core.config import get_settings

engine = create_engine(get_settings().database_url, future=True)
with engine.connect() as conn:
    exists = conn.execute(
        text(
            "SELECT EXISTS ("
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name='alembic_version'"
            ")"
        )
    ).scalar_one()
print("1" if exists else "0")
PY
)"

if [ "$TABLE_COUNT" -gt 0 ] && [ "$HAS_ALEMBIC" = "0" ]; then
  echo "Detected pre-existing schema without alembic_version; stamping baseline..."
  alembic stamp 0001_initial_schema
fi

echo "Running alembic upgrade head..."
alembic upgrade head
echo "Migration complete."
