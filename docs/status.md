# Current status, 26 October 2026

Release preparation starts from upstream **f45e2ff**, which adds per-account
persistence. The older ba865ed/bf659a7 audit is not the state of this release:
accounts, profiles and rooms can now survive restarts. The real-process smoke
test verifies SQLite persistence, without contacting Supabase.

| Capability | State / evidence |
|---|---|
| Separate Profile and Calendar | Implemented; account isolation and persistence tests |
| Editable timetable, exams and unavailable periods | Implemented; owner/API/browser paths |
| Room discovery and membership | Implemented; fixture venues in offline mode |
| Session → Schedule | Implemented; source projection and five-second polling |
| PostgreSQL / Supabase | Adapter present; local dialect checks; no live cloud validation during release work |
| Omnara | Optional clients; disabled/mocked here; matching prompt remains stand-in |
| Google Calendar, live email and venue booking | Not enabled in ordinary application |
| Public website | No deployment performed by this release task |
| GitHub Actions matrix | Workflow supplied; remote results require a future push |

## Known limitations

- Request dates and rooms are anchored to the October 2026 demo week.
- Login is not campus verification. Sample credentials are for local use. Public
  service use needs recovery, abuse controls and consistent CSRF coverage across
  every mutation route; Calendar editor CSRF does not cover the whole product.
- Random default signing keys log users out after process restart. A host should
  configure a stable private key and HTTPS cookies.
- Room JSON load/save needs transactional concurrency tests before multi-worker
  usage. Offline tests do not prove race freedom or production-scale performance.
- PostgreSQL compilation and RLS statements are not a live Supabase security,
  pooler, backup or durability audit. This task runs no shared migrations.
- Four-tool Agent and export/approval designs exceed the enabled normal app.
  Old open development branches are not release dependencies.
- No live-service latency, model-quality or matching-improvement result is claimed.

## Next engineering priorities

1. Remove the fixed demonstration-week dependency from date interpretation.
2. Review production migrations and test PostgreSQL room-capacity contention.
3. Complete auth, CSRF, retention and sample-data separation before public hosting.
4. Replace the stand-in prompt and compare model choices with a deterministic
   baseline using a held-out synthetic evaluation set.
