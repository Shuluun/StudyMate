# Public interactive demo

This deployment runs the complete team's FastAPI UI, using **fictional data only**.
The landing page offers a one-click guest experience; it does not collect accounts,
email addresses, OAuth credentials or API keys. Original team credits and repository
links appear on every page. The upstream team repository is not a deployment target.

## Render Free configuration

- Repository: `https://github.com/Shuluun/StudyMate`, branch `main`
- Runtime: Python 3.13.5, Free instance, **one process**
- Build: `pip install -r requirements-lock.txt`
- Start: `python -m app.public_demo`
- Health: `/api/health`
- Optional: random `STUDYMATE_SESSION_SECRET`, at least 32 characters. The app
  otherwise generates a new random key each boot. Never commit its value.
- `render.yaml` records the same settings. No paid disk or database is requested.

The public entrypoint binds `0.0.0.0:$PORT`, forces offline providers, local SQLite
and HTTPS-only signed cookies. It ignores developer cloud database configuration.
It does not trust forwarded proxy headers; form origins are checked against
Render's `RENDER_EXTERNAL_URL`. A custom domain requires explicitly configuring
that canonical origin in the application before using it.

Every guest gets a server-generated directory with separate team and calendar
SQLite databases. Request context routes the existing adapters to that sandbox;
database queries, profile caches, room seeds and schedule runtimes cannot borrow
another visitor's data. Form mutations require CSRF tokens. Retired global-state
invitation endpoints, Google adapters and the legacy matching API are unavailable;
the current Session room board, local discovery, Profile and timetable remain.

## Limits

- This is a demonstration, not a production student service. Use sample text only.
- Changes last within the guest's browser sandbox, expire after 30 minutes of
  inactivity, and reset on server restart/redeploy. Opening a new guest copy cleans
  expired sandboxes. At most 32 copies can be active; further guests see a retry page.
- Render Free sleeps after 15 minutes without traffic; waking can take about a
  minute. Its filesystem is ephemeral. This is why the site promises temporary
  demo data rather than permanent hosted accounts.
- SQLite isolation is per server process. Run exactly one worker; horizontal scaling
  and durable multi-user storage need a different deployment composition.
- No real calendars, notifications, LLM ranking or external geocoding run here.
  Natural-language discovery uses the existing local parser and seeded places.
- Do not enter personal information. Basic abuse limits are not a full production
  security review or a guarantee of uptime under malicious traffic.

## Verification

```bash
python -m pytest -q
python tools/smoke.py
python tools/smoke_public.py --url https://YOUR-SERVICE.onrender.com
```

The public smoke uses two fresh cookie jars, edits synthetic busy time, opens and
closes a room, verifies that reservations reach Schedule, and checks the second
visitor cannot see those changes. It never accesses a real calendar or sends mail.
Local HTTP preview (for developers only):

```bash
python -c "import uvicorn; from app.public_demo import create_public_app; uvicorn.run(create_public_app(secure=False), host='127.0.0.1', port=8033)"
```

Do not expose that HTTP preview as a public server. Published hosts use the secure
entrypoint above. Existing local `python -m app.demo` retains persistent user data;
the temporary public entrypoint does not change that behavior.

Platform limits: [Render Free](https://render.com/docs/free),
[default environment variables](https://render.com/docs/environment-variables).
