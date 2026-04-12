## Alembic Migration Workflow

- Source of truth for schema changes is `backend/alembic/versions`.
- Apply migrations with `alembic upgrade head` (or `/app/scripts/migrate.sh` in Docker).
- Do not rely on ORM `create_all` in staging/production.
- Every schema change should include:
  - a forward migration
  - a downgrade path when practical
  - matching model updates in `app/models` / `app/messaging/models.py`

### Realtime messaging revisions

- `0002_realtime_messaging_phase1` creates:
  - `conversations`
  - `conversation_members`
  - `messages`
  - `message_recipients`
  - `outbox_events`
- `0003_outbox_relay_hardening` adds outbox processing columns/index.
- `0004_realtime_messaging_indexes` adds hot-path indexes and sequence uniqueness.
- `0005_notification_delivery_tbls` adds:
  - `notification_devices`
  - `notification_attempts`
