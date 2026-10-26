# Publishing this team project

Suggested repository title: **StudyMate**.

Suggested description:

> A constraint-aware study-group planner with private schedules, persistent
> profiles, room membership, and optional Omnara-assisted discovery. FastAPI,
> SQLite/PostgreSQL, and a reproducible offline demo.

Suggested topics: `fastapi`, `python`, `scheduling`, `calendar`, `study-groups`,
`postgresql`, `sqlite`, `hackathon`.

## Preserve provenance

The preferred personal showcase is a fork of the upstream team repository, with
the public-release preparation branch applied. Keep the original LICENSE,
CONTRIBUTORS and upstream relationship. Team main and old development branches
do not need to be overwritten. A fork accurately represents collaboration while
letting you improve documentation and demo quality on your own copy.

If you publish the clean source ZIP as a new repository instead, it contains no
Git history. Keep attribution and explicitly link upstream. Do not label the
entire app as your sole original work. The source manifest records its provenance.

## Before publishing

- Review README, screenshots and CONTRIBUTORS; all screenshots use fictional data.
- Confirm the source export contains no private `.env`, credentials or databases.
- Run the full tests, real-process smoke and dependency check.
- Choose the destination account/repository, then publish the reviewed source.
- Inspect the actual GitHub README and CI results after the push. A public source
  repository is distinct from a public hosted website.

## What makes this a useful portfolio project

The demonstrable work is a complete product path: separate accounts and profiles,
server-checked time constraints, room discovery and lifecycle, synchronized
timetables, persistent state, and an executable offline reproduction. Explain
the tradeoffs: deterministic hard rules versus model suggestions, private versus
shared data, poll-based updates, and the current concurrency/date limitations.
Do not replace evidence with claims of production readiness or unmeasured AI gains.
