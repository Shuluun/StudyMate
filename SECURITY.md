# Security scope

This is a hackathon/research prototype with a loopback-only offline launcher.
Use synthetic data. The fictional demo account is not an appropriate credential
for a public deployment.

The normal app uses a random session-signing secret unless a private
`STUDYMATE_SESSION_SECRET` of at least 32 characters is supplied. Use a stable
private secret and `STUDYMATE_SECURE_COOKIES=1` on HTTPS. These settings alone
do not make the prototype production-ready.

Before public service use, review CSRF consistently across all account/Profile/
Session endpoints, add login abuse controls and recovery, segregate demo accounts,
establish retention/deletion policy, and test room capacity/membership transactions
under concurrent requests. Room storage currently loads/saves JSON room sets;
it is not a demonstrated multi-worker booking lock.

The PostgreSQL adapter enables RLS on application tables. The server's owner
connection can bypass RLS, so server authorization still matters. Local checks do
not prove a particular Supabase project's permissions, backups or isolation.

Do not post secrets or private records in GitHub issues. Contact maintainers
through an available private channel. No monitored security mailbox or response
time commitment is advertised.
