# Configuration

## Offline preview

`python -m app.demo --data-dir data/demo --port 8020` overrides database URLs to
local SQLite, sets `STUDYMATE_OFFLINE=1`, and binds only to 127.0.0.1. No provider
credentials are needed. A private `.env` cloud URL cannot redirect this launcher
to shared data. Use one process for the demo.

## Configured development

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8020 --no-access-log
```

| Variable | Effect |
|---|---|
| `DATABASE_URL` | SQLite/PostgreSQL URL; otherwise local account/Profile/room file |
| `STUDYMATE_CALENDAR_DB` | Optional Calendar DB override; otherwise cloud URL or local Calendar file |
| `STUDYMATE_OFFLINE=1` | Disable map lookups and implicit Omnara clients |
| `STUDYMATE_SESSION_SECRET` | Stable private signing key, at least 32 characters; random by default |
| `STUDYMATE_SECURE_COOKIES=1` | HTTPS-only cookie; unsuitable for plain loopback HTTP |
| `STUDYMATE_DB=memory` | Nonpersistent account/Profile/room mode for tests |

`DATABASE_URL` is read from the environment or root `.env` by `app.db`. Other
modules have separate configuration readers. Configure variables in the shell/host,
not by assuming a generic dotenv loader. `.env.example` has no secret values.

## PostgreSQL / Supabase

The server uses a private psycopg connection URL, not a public/anon API key.
`postgres://` and `postgresql://` normalize to the psycopg SQLAlchemy dialect.
Prepared-statement reuse is disabled for transaction-pooler compatibility.

Adapters currently initialize tables and RLS. Review schema/permissions and get
team approval before applying them to shared data. This release work performs
no cloud migrations and verifies no live Supabase configuration.

## Optional maps/models

Review `app/places.py`, `app/omnara_client.py` and `app/advise.py` before opting in.
Ordinary online map lookup can contact OpenStreetMap without a Google key; the
offline launcher avoids both. Omnara requires private project/model configuration.

Google Calendar connect/refresh/export routes are intentionally absent from the
ordinary app. Earlier Google documents are historical notes, not setup instructions.
