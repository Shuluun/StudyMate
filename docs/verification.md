# Verification record

Release preparation date: **26 October 2026**. Upstream base: **f45e2ff**.
All data used in this task were synthetic. No real calendar, map, model, mail or
shared Supabase operation was performed.

## Environment and commands

An independent Windows Python **3.13.5** virtual environment was created, then
installed with the project requirements and existing constraints. Its exact
resolved versions are saved in `requirements-lock.txt`.

```text
python -m pip install -r requirements-lock.txt
python -m pytest -q --junitxml=test-results.xml
python tools/smoke.py
python -m pip check
node --check app/static/calendar.js
node --check app/static/range.js
```

The full source suite passed **407 tests** before the source-export tests were
added. Package filtering checks passed separately. The final exported-copy result
is recorded below after execution; those earlier results are not summed into a
claim of an unexecuted full suite.

## Real-process integration

`tools/smoke.py` returned `PASS` for six flows:

1. Register two independent accounts and save their profiles.
2. Save a private schedule edit and reject another owner's target.
3. Host/join a room and observe it in both schedules.
4. Reschedule as host and observe the other member's updated block.
5. Stop and restart the actual Uvicorn process; sign in and verify accounts,
   profiles, schedules and rooms persist.
6. Leave and close an empty room; remove the corresponding reservations.

It uses temporary SQLite files and localhost HTTP, not simulated restart by just
clearing Python caches. Those files are discarded after the test.

## Browser checks

The isolated port-8032 offline preview was used to sign in as fictional Maya,
submit a natural-language request, host a Monday room, join a Wednesday room,
create an exam in the timetable, and inspect the resulting blocks. The timetable
and room-board PNGs in `docs/screenshots/` are actual screenshots of those actions.
No browser JavaScript errors were observed in that preview.

## Not verified here

Live PostgreSQL/Supabase operations, production RLS effectiveness, multi-worker
room races, public hosting, live Omnara quality/latency, real Google Calendar,
email delivery and venue booking are not claimed. The workflow's Linux/Python
matrix is a future CI configuration, not a completed remote run. Two current
dependency deprecation warnings concern HTTPX integrations; they are not test failures.

## Exported-copy verification

The clean ZIP was extracted into a new directory without a `.git`, `.env`, data
directory, virtual environment, or original-working-copy imports. Using the
independent dependency environment, that copy passed **431 tests, 2 warnings**.
The Windows check explicitly created its `.tmp` directory before passing a nested
pytest `--basetemp`; ordinary `python -m pytest -q` does not require this option.

The exported copy's real-process smoke test passed all six flows. A transient
Windows file-lock during temporary SQLite cleanup was addressed with bounded
retries on the tool's own verified scratch directory, then the smoke was rerun
successfully. Database or service failures are not ignored by this retry.

The export uses an allowlist and checks credential-like content; database files,
SQLite journals, `.env`, key files, nested ZIPs, CSV exports, caches and virtual
environments are excluded. The generated manifest hashes each file, records the
source commit and whether the working tree was dirty, and discloses that Git
history is not included. This is not a guarantee that all old Git commits are secret-free.
