"""Public, offline team demo. Each browser gets a temporary SQLite sandbox.

Run with python -m app.public_demo. This is not a production account system.
No real calendars, cloud databases, mail or model providers are enabled.
"""
import asyncio
import os
import tempfile
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from secrets import compare_digest, token_urlsafe

from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app import db


@dataclass
class Sandbox:
    directory: Path
    touched: float
    engine: object = None
    runtime: object = None
    active: int = 0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class PublicDemo:
    def __init__(self, directory, *, capacity=32, ttl=1800, clock=time.monotonic, origin=None):
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.capacity, self.ttl, self.clock, self.origin = capacity, ttl, clock, origin
        self.sandboxes = {}

    def _close(self, sandbox):
        from app import store
        if sandbox.runtime:
            sandbox.runtime.repository.close()
        if sandbox.engine is not None:
            url = str(sandbox.engine.url)
            sandbox.engine.dispose()
            store._seeded.discard(url)
            for cache in (store._cache, store._room_rankings):
                for key in list(cache):
                    if isinstance(key, tuple) and key[0] == url:
                        cache.pop(key, None)
        # Only files inside this server-created sandbox, never user paths.
        for path in sandbox.directory.iterdir():
            if path.is_file() and path.resolve().parent == sandbox.directory:
                path.unlink()
        sandbox.directory.rmdir()

    def expire(self):
        for key, sandbox in list(self.sandboxes.items()):
            if not sandbox.active and self.clock() - sandbox.touched >= self.ttl:
                self._close(sandbox)
                del self.sandboxes[key]

    def close(self):
        for sandbox in self.sandboxes.values():
            self._close(sandbox)
        self.sandboxes.clear()

    def create(self):
        self.expire()
        if len(self.sandboxes) >= self.capacity:
            return None
        key = token_urlsafe(24)
        directory = self.directory / key
        directory.mkdir()
        self.sandboxes[key] = Sandbox(directory, self.clock())
        return key

    async def csrf_ok(self, request):
        origin = request.headers.get("origin")
        expected = self.origin or str(request.base_url).rstrip("/")
        if origin and origin != expected:
            return False
        supplied = request.headers.get("x-csrf-token", "")
        if not supplied and request.headers.get("content-type", "").startswith("application/x-www-form-urlencoded"):
            await request.body()
            supplied = str((await request.form()).get("csrf_token", ""))
        return compare_digest(supplied.encode(), request.session["calendar_editor_csrf"].encode())

    async def handle(self, request, call_next):
        from app.scheduling.context import local_subject
        from app.scheduling.runtime import build_runtime, request_runtime
        path = request.url.path
        if path == "/api/health" or path.startswith("/static/"):
            return await call_next(request)
        request.session.setdefault("calendar_editor_csrf", token_urlsafe(32))
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            body = await request.body()
            if len(body) > 65536:
                return JSONResponse({"detail": "DEMO_INPUT_TOO_LARGE"}, 413)
            if not await self.csrf_ok(request):
                if path == "/demo/start":
                    # A cold start/redeploy can invalidate the old landing cookie.
                    # Refresh the form without creating or changing any sandbox.
                    return RedirectResponse("/?session=refreshed", 303)
                return JSONResponse({"detail": "CSRF_REQUIRED"}, 403)
        # Retired invitations use process-wide fixture state. They are not part
        # of the room board and must not be exposed by this multi-visitor host.
        if path.startswith(("/calendar/", "/schedule/google", "/api/match")) or path in {
            "/session/draft", "/session/swap-person", "/session/swap-place",
            "/session/confirm", "/session/calendar",
        }:
            return JSONResponse({"detail": "NOT_AVAILABLE_IN_PUBLIC_DEMO"}, 404)
        key = request.session.get("demo_sandbox")
        sandbox = self.sandboxes.get(key) if isinstance(key, str) else None
        if sandbox and self.clock() - sandbox.touched >= self.ttl and not sandbox.active:
            self.expire()
            sandbox = None
        if path == "/demo/start" and request.method == "POST":
            if sandbox is None:
                key = self.create()
                if key is None:
                    return HTMLResponse("Demo is busy. Please try again in 30 minutes.", 503,
                                        headers={"Retry-After": "1800"})
            request.session.clear()
            request.session.update(demo_sandbox=key, user={"id": "u_maya", "name": "Maya Chen"},
                                   calendar_editor_csrf=token_urlsafe(32))
            return RedirectResponse("/schedule?day=2026-10-26", 303)
        if path in {"/", "/login", "/register"}:
            if request.method != "GET":
                return JSONResponse({"detail": "DEMO_ACCOUNTS_ONLY"}, 403)
            if sandbox:
                return RedirectResponse("/schedule?day=2026-10-26", 303)
            from app.web import render
            return render(request, "public_demo.html")
        if sandbox is None:
            request.session.pop("user", None)
            return RedirectResponse("/", 303)
        sandbox.active += 1
        try:
            async with sandbox.lock:
                sandbox.touched = self.clock()
                if sandbox.engine is None:
                    url = f"sqlite+pysqlite:///{(sandbox.directory / 'team.db').as_posix()}"
                    sandbox.engine = db.make_engine(url)
                    db.metadata.create_all(sandbox.engine)
                    sandbox.runtime = build_runtime(f"sqlite+pysqlite:///{(sandbox.directory / 'calendar.db').as_posix()}")
                engine_token = db.request_engine.set(sandbox.engine)
                runtime_token = request_runtime.set(sandbox.runtime)
                subject_token = local_subject.set("u_maya")
                try:
                    response = await call_next(request)
                    response.headers["Cache-Control"] = "no-store"
                    response.headers["X-Content-Type-Options"] = "nosniff"
                    response.headers["Referrer-Policy"] = "same-origin"
                    response.headers["Content-Security-Policy"] = "frame-ancestors 'none'; form-action 'self'; base-uri 'self'"
                    return response
                finally:
                    local_subject.reset(subject_token)
                    request_runtime.reset(runtime_token)
                    db.request_engine.reset(engine_token)
        finally:
            sandbox.active -= 1


def create_public_app(directory=None, *, secure=True, capacity=32, ttl=1800, clock=time.monotonic, origin=None):
    # Override once at boot, never per visitor. Ignore local .env credentials.
    from app.demo import configure
    directory = Path(directory or tempfile.mkdtemp(prefix="studymate-public-"))
    configure(directory)
    os.environ["STUDYMATE_SECURE_COOKIES"] = "1" if secure else "0"
    from app.main import create_app
    demo = PublicDemo(directory, capacity=capacity, ttl=ttl, clock=clock,
                      origin=origin or os.environ.get("RENDER_EXTERNAL_URL"))
    app = create_app(public_demo=demo)

    @asynccontextmanager
    async def lifespan(app):
        try:
            yield
        finally:
            demo.close()
    app.router.lifespan_context = lifespan
    return app


def main():
    import uvicorn
    uvicorn.run(create_public_app(), host="0.0.0.0", port=int(os.environ.get("PORT", "8080")),
                access_log=False, proxy_headers=False)


if __name__ == "__main__":
    main()
