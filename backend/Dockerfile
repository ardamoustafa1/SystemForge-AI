FROM python:3.12-slim AS base

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY pyproject.toml /app/pyproject.toml
RUN pip install uv && uv pip install --system . && useradd -m appuser

FROM base AS runtime
COPY app /app/app
COPY assets /app/assets
COPY scripts /app/scripts
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini
EXPOSE 8000
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base AS test
COPY app /app/app
COPY assets /app/assets
COPY tests /app/tests
COPY scripts /app/scripts
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini
COPY pytest.ini /app/pytest.ini
RUN uv pip install --system .[dev]
CMD ["python", "-m", "pytest", "tests", "-q"]
