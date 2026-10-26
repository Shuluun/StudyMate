"""Multi-visitor deployment checks against the real team routers and SQLite."""
import json
import re

import pytest
from fastapi.testclient import TestClient

from app import db
from app.public_demo import create_public_app

DAY = "2026-10-27"


@pytest.fixture
def public_app(tmp_path, monkeypatch):
    for key in ("DATABASE_URL", "STUDYMATE_CALENDAR_DB", "STUDYMATE_DB", "STUDYMATE_OFFLINE",
                "STUDYMATE_CALENDAR_MODE", "STUDYMATE_SECURE_COOKIES"):
        monkeypatch.setenv(key, "unused-synthetic-cloud-config")
    app = create_public_app(tmp_path / "public")
    yield app
    app.state.public_demo.close()


def start(client):
    response = client.get("/")
    token = re.search(r'name="csrf_token" value="([^"]+)"', response.text)[1]
    response = client.post("/demo/start", data={"csrf_token": token})
    assert response.status_code == 200
    return headers(client)


def headers(client):
    page = client.get("/schedule?day=" + DAY)
    assert page.status_code == 200
    data = json.loads(re.search(r'<script id="calendar-week-data" type="application/json">(.*?)</script>', page.text, re.S)[1])
    return {"X-CSRF-Token": data["csrf"]}


def entries(client):
    response = client.get("/api/schedule/week?day=" + DAY)
    assert response.status_code == 200
    return response.json()["entries"]


def test_two_visitors_cannot_share_schedule_profile_or_rooms(public_app):
    with TestClient(public_app, base_url="https://testserver") as a, TestClient(public_app, base_url="https://testserver") as b:
        first = start(a)
        assert a.post("/api/schedule/entry", headers=first, json={"kind": "busy", "starts_at": DAY+"T15:30", "ends_at": DAY+"T16:00"}).status_code == 200
        busy_id = next(e["id"] for e in entries(a) if e["kind"] == "busy")
        # Creating a later sandbox must seed from original rooms, not a's changes.
        response = a.post("/session/rooms", headers=first, data={"course_id": "math54", "starts_at": DAY+"T13:00", "ends_at": DAY+"T14:00", "place_type": "library", "group_size": "3"}, follow_redirects=False)
        assert response.status_code == 303 and "error=" not in response.headers["location"]
        room_id = next(e["id"] for e in entries(a) if e["kind"] == "session")
        second = start(b)
        assert not any(e["id"] in {busy_id, room_id} for e in entries(b))
        assert b.post("/session/rooms/"+room_id+"/join", headers=second, follow_redirects=False).status_code == 303
        assert not any(e["id"] == room_id for e in entries(b))
        assert a.put("/api/profile/me", headers=first, json={"major": "Physics", "year": 2, "courses": "Math 54", "street_address": "UC Berkeley", "radius_meters": 1500, "group_min": 2, "group_max": 3, "study_styles": ["talk"], "place_types": ["library"]}).status_code == 200
        assert a.get("/api/profile/me").json()["major"] == "Physics"
        assert b.get("/api/profile/me").json()["major"] != "Physics"
        assert a.post("/session/rooms/"+room_id+"/leave", headers=first, follow_redirects=False).status_code == 303
        assert not any(e["id"] == room_id for e in entries(a))
        assert db.request_engine.get() is None


def test_forms_have_csrf_credits_and_no_real_account_signup(public_app):
    with TestClient(public_app, base_url="https://testserver") as client:
        page = client.get("/")
        assert "Original team repository" in page.text and "Jiayang Wu" in page.text
        assert "Create account" not in page.text
        assert "secure" in page.headers["set-cookie"].lower() and "httponly" in page.headers["set-cookie"].lower()
        refused = client.post("/demo/start", follow_redirects=False)
        assert refused.status_code == 303 and refused.headers["location"] == "/?session=refreshed"
        assert not public_app.state.public_demo.sandboxes
        token = start(client)
        for path in ("/profile", "/session", "/schedule"):
            page = client.get(path)
            for form in re.findall(r'<form\b[^>]*method="post".*?</form>', page.text, re.S):
                assert 'name="csrf_token"' in form
        assert client.post("/register", headers=token, data={"email": "unused@example.invalid"}).status_code == 403
        assert client.put("/api/profile/me", json={}).status_code == 403
        assert client.post("/session/interpret", headers={**token, "Origin": "https://untrusted.example"}, data={"sentence": "CS 61A"}).status_code == 403
        assert client.get("/schedule/google-setup").status_code == 404
        assert client.post("/session/confirm", headers=token).status_code == 404


def test_canonical_https_origin_behind_proxy(public_app):
    public_app.state.public_demo.origin = "https://studymate.example"
    with TestClient(public_app, base_url="https://testserver") as client:
        token = start(client)
        response = client.post("/api/schedule/entry", headers={**token, "Origin": "https://studymate.example"}, json={"kind": "busy", "starts_at": DAY+"T10:00", "ends_at": DAY+"T11:00"})
        assert response.status_code == 200
        assert client.post("/api/schedule/entry", headers={**token, "Origin": "http://studymate.example"}, json={}).status_code == 403


def test_expiry_and_capacity_are_bounded(public_app):
    demo = public_app.state.public_demo
    now = [0]
    demo.clock = lambda: now[0]
    demo.capacity, demo.ttl = 1, 30
    with TestClient(public_app, base_url="https://testserver") as a, TestClient(public_app, base_url="https://testserver") as b:
        start(a)
        page = b.get("/")
        token = re.search(r'name="csrf_token" value="([^"]+)"', page.text)[1]
        assert b.post("/demo/start", data={"csrf_token": token}).status_code == 503
        now[0] = 31
        assert b.post("/demo/start", data={"csrf_token": token}).status_code == 200
        assert a.get("/api/profile/me", follow_redirects=False).headers["location"] == "/"
        assert len(demo.sandboxes) == 1


def test_cookie_forgery_and_external_config_are_ignored(public_app):
    import os
    assert os.environ["STUDYMATE_OFFLINE"] == "1"
    assert os.environ["DATABASE_URL"].startswith("sqlite+pysqlite:///")
    assert os.environ["STUDYMATE_DB"] == "local"
    with TestClient(public_app, base_url="https://testserver") as client:
        client.cookies.set("studymate_demo", "forged-sandbox-cookie")
        assert client.get("/api/profile/me", follow_redirects=False).headers["location"] == "/"
