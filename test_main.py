from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

import main
from main import app

client = TestClient(app)


def test_create_and_list_habit():
    r = client.post("/habits", json={"name": "Read 20 minutes"})
    assert r.status_code == 200
    hid = r.json()["id"]
    r2 = client.get("/habits")
    assert r2.status_code == 200
    assert any(h["id"] == hid for h in r2.json())


def test_checkin_flow():
    hid = client.post("/habits", json={"name": "Stretch"}).json()["id"]
    r = client.post(f"/habits/{hid}/checkin", json={"day": "2026-09-22"})
    assert r.status_code == 200
    r2 = client.get(f"/habits/{hid}/checkins")
    assert r2.json() == ["2026-09-22"]


def test_checkin_unknown_habit_404():
    r = client.post("/habits/99999/checkin", json={"day": "2026-09-22"})
    assert r.status_code == 404


# --- Streak tests ---

FIXED_TODAY = date(2026, 9, 22)


@pytest.fixture
def fixed_clock(monkeypatch):
    """Freeze the app's clock so streak tests never depend on the real date."""
    monkeypatch.setattr(main, "_today", lambda: FIXED_TODAY)


def test_streak_unknown_habit_404(fixed_clock):
    r = client.get("/habits/99999/streak")
    assert r.status_code == 404


def test_streak_no_checkins_is_zero(fixed_clock):
    hid = client.post("/habits", json={"name": "No checkins habit"}).json()["id"]
    r = client.get(f"/habits/{hid}/streak")
    assert r.status_code == 200
    assert r.json() == {"habit_id": hid, "streak": 0}


def test_streak_today_only(fixed_clock):
    hid = client.post("/habits", json={"name": "Today only"}).json()["id"]
    today = FIXED_TODAY.isoformat()
    client.post(f"/habits/{hid}/checkin", json={"day": today})
    r = client.get(f"/habits/{hid}/streak")
    assert r.status_code == 200
    assert r.json() == {"habit_id": hid, "streak": 1}


def test_streak_consecutive_days_ending_today(fixed_clock):
    hid = client.post("/habits", json={"name": "Three day streak"}).json()["id"]
    today = FIXED_TODAY
    for delta in range(3):
        day = (today - timedelta(days=delta)).isoformat()
        client.post(f"/habits/{hid}/checkin", json={"day": day})
    r = client.get(f"/habits/{hid}/streak")
    assert r.status_code == 200
    assert r.json() == {"habit_id": hid, "streak": 3}


def test_streak_gap_resets_to_zero_when_today_missing(fixed_clock):
    hid = client.post("/habits", json={"name": "Gap streak"}).json()["id"]
    today = FIXED_TODAY
    # Check in yesterday and two days ago but NOT today
    for delta in range(1, 3):
        day = (today - timedelta(days=delta)).isoformat()
        client.post(f"/habits/{hid}/checkin", json={"day": day})
    r = client.get(f"/habits/{hid}/streak")
    assert r.status_code == 200
    # No check-in today → streak is broken at today
    assert r.json() == {"habit_id": hid, "streak": 0}


def test_streak_non_consecutive_days(fixed_clock):
    hid = client.post("/habits", json={"name": "Non-consecutive"}).json()["id"]
    today = FIXED_TODAY
    # Check in today and 3 days ago (gap on day 1 and 2)
    client.post(f"/habits/{hid}/checkin", json={"day": today.isoformat()})
    client.post(f"/habits/{hid}/checkin", json={"day": (today - timedelta(days=3)).isoformat()})
    r = client.get(f"/habits/{hid}/streak")
    assert r.status_code == 200
    # Streak should be 1 (only today; gap before yesterday breaks chain)
    assert r.json() == {"habit_id": hid, "streak": 1}


def test_streak_duplicate_checkins_not_double_counted(fixed_clock):
    hid = client.post("/habits", json={"name": "Duplicate days"}).json()["id"]
    today = FIXED_TODAY
    yesterday = (today - timedelta(days=1)).isoformat()
    # Insert today twice and yesterday twice
    for _ in range(2):
        client.post(f"/habits/{hid}/checkin", json={"day": today.isoformat()})
        client.post(f"/habits/{hid}/checkin", json={"day": yesterday})
    r = client.get(f"/habits/{hid}/streak")
    assert r.status_code == 200
    assert r.json() == {"habit_id": hid, "streak": 2}


def test_streak_ignores_malformed_stored_day(fixed_clock):
    """A bad 'day' already in the DB must not crash the streak endpoint."""
    hid = client.post("/habits", json={"name": "Messy data"}).json()["id"]
    client.post(f"/habits/{hid}/checkin", json={"day": FIXED_TODAY.isoformat()})
    client.post(f"/habits/{hid}/checkin", json={"day": "not-a-date"})
    r = client.get(f"/habits/{hid}/streak")
    assert r.status_code == 200
    assert r.json() == {"habit_id": hid, "streak": 1}
