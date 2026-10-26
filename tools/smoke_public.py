"""Exercise only temporary guest sandboxes on a public StudyMate demo."""
import argparse
import json
import re
from urllib.parse import urlsplit

import httpx

DAY = "2026-10-27"


def csrf(client):
    page = client.get("/schedule?day=" + DAY)
    assert page.status_code == 200
    data = json.loads(re.search(r'<script id="calendar-week-data" type="application/json">(.*?)</script>', page.text, re.S)[1])
    return {"X-CSRF-Token": data["csrf"], "Origin": str(client.base_url).rstrip("/")}


def start(client):
    page = client.get("/")
    assert page.status_code == 200 and "Original team repository" in page.text
    token = re.search(r'name="csrf_token" value="([^"]+)"', page.text)[1]
    assert client.post("/demo/start", data={"csrf_token": token}, headers={"Origin": str(client.base_url).rstrip("/")}).status_code == 200
    return csrf(client)


def entries(client):
    response = client.get("/api/schedule/week?day=" + DAY)
    assert response.status_code == 200
    return response.json()["entries"]


def run(url):
    parsed = urlsplit(url)
    if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost"}):
        raise ValueError("Public smoke requires HTTPS; HTTP is allowed only on loopback")
    checks = []
    with httpx.Client(base_url=url, follow_redirects=True, timeout=90) as a, httpx.Client(base_url=url, follow_redirects=True, timeout=90) as b:
        first = start(a)
        assert a.get("/api/health").json() == {"ok": True}
        checks.append("guest entry and team credits")
        assert a.post("/api/schedule/entry", headers=first, json={"kind": "busy", "starts_at": DAY+"T15:30", "ends_at": DAY+"T16:00"}).status_code == 200
        busy = next(e["id"] for e in entries(a) if e["kind"] == "busy")
        response = a.post("/session/rooms", headers=first, data={"course_id": "math54", "starts_at": DAY+"T13:00", "ends_at": DAY+"T14:00", "place_type": "library", "group_size": "3"}, follow_redirects=False)
        assert response.status_code == 303 and "error=" not in response.headers["location"]
        room = next(e["id"] for e in entries(a) if e["kind"] == "session")
        checks.append("schedule editing and Session reservations")
        start(b)
        assert not any(e["id"] in {busy, room} for e in entries(b))
        checks.append("two independent guest cookie jars cannot share changes")
        assert a.post("/session/rooms/"+room+"/leave", headers=first, follow_redirects=False).status_code == 303
        assert not any(e["id"] == room for e in entries(a))
        assert a.post("/api/schedule/entry", headers={**first, "Origin": "https://untrusted.example"}, json={}).status_code == 403
        assert a.get("/schedule/google-setup").status_code == 404
        assert all(a.get(path).status_code == 200 for path in ("/profile", "/session", "/schedule"))
        checks.append("leaving releases reservations; CSRF and disabled Google routes")
    print(json.dumps({"result": "PASS", "url": url, "transport": parsed.scheme, "checks": checks, "external_calendar_or_model_used": False}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    run(parser.parse_args().url.rstrip("/"))
