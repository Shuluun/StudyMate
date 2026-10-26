# Contributing

Start a feature branch from the latest upstream `main`. Preserve existing work;
do not merge old integration/Google/Agent branches just to clear conflicts.

Install `requirements-lock.txt` in an isolated Python 3.11+ environment. Run
`python -m pytest -q`, `python tools/smoke.py`, and `python -m pip check`.
Tests use offline/memory controls and temporary SQLite files. Never point tests
at shared Supabase data.

Scheduling changes should cover interval boundaries, durations, DST, unknown
calendar state and sanitized output as relevant. Session changes must preserve
membership, host permissions, conflict checks and Schedule synchronization.
Keep ownership in the existing modules; do not add a second identity or booking system.

Include the problem, final change, actual tests and remaining limits in a PR.
Keep keys, `.env`, OAuth JSON, tokens, real schedules, account exports, databases
and logs out of commits. Source export scans the current file set, not all history.
Check the personal fork's latest Actions run before describing its CI matrix as verified.
