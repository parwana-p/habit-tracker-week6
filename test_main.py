from datetime import date, timedelta

from fastapi.testclient import TestClient

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


def test_streak_unknown_habit_404():
    r = client.get("/habits/99999/streak")
    assert r.status_code == 404


def test_streak_no_checkins_is_zero():
    hid = client.post("/habits", json={"name": "No checkins habit"}).json()["id"]
    r = client.get(f"/habits/{hid}/streak")
    assert r.status_code == 200
    assert r.json() == {"habit_id": hid, "streak": 0}


def test_streak_today_only():
    hid = client.post("/habits", json={"name": "Today only"}).json()["id"]
    today = date.today().isoformat()
    client.post(f"/habits/{hid}/checkin", json={"day": today})
    r = client.get(f"/habits/{hid}/streak")
    assert r.status_code == 200
    assert r.json() == {"habit_id": hid, "streak": 1}


def test_streak_consecutive_days_ending_today():
    hid = client.post("/habits", json={"name": "Three day streak"}).json()["id"]
    today = date.today()
    for delta in range(3):
        day = (today - timedelta(days=delta)).isoformat()
        client.post(f"/habits/{hid}/checkin", json={"day": day})
    r = client.get(f"/habits/{hid}/streak")
    assert r.status_code == 200
    assert r.json() == {"habit_id": hid, "streak": 3}


def test_streak_gap_resets_to_zero_when_today_missing():
    hid = client.post("/habits", json={"name": "Gap streak"}).json()["id"]
    today = date.today()
    # Check in yesterday and two days ago but NOT today
    for delta in range(1, 3):
        day = (today - timedelta(days=delta)).isoformat()
        client.post(f"/habits/{hid}/checkin", json={"day": day})
    r = client.get(f"/habits/{hid}/streak")
    assert r.status_code == 200
    # No check-in today → streak is broken at today
    assert r.json() == {"habit_id": hid, "streak": 0}


def test_streak_non_consecutive_days():
    hid = client.post("/habits", json={"name": "Non-consecutive"}).json()["id"]
    today = date.today()
    # Check in today and 3 days ago (gap on day 1 and 2)
    client.post(f"/habits/{hid}/checkin", json={"day": today.isoformat()})
    client.post(f"/habits/{hid}/checkin", json={"day": (today - timedelta(days=3)).isoformat()})
    r = client.get(f"/habits/{hid}/streak")
    assert r.status_code == 200
    # Streak should be 1 (only today; gap before yesterday breaks chain)
    assert r.json() == {"habit_id": hid, "streak": 1}


def test_streak_duplicate_checkins_not_double_counted():
    hid = client.post("/habits", json={"name": "Duplicate days"}).json()["id"]
    today = date.today()
    yesterday = (today - timedelta(days=1)).isoformat()
    # Insert today twice and yesterday twice
    for _ in range(2):
        client.post(f"/habits/{hid}/checkin", json={"day": today.isoformat()})
        client.post(f"/habits/{hid}/checkin", json={"day": yesterday})
    r = client.get(f"/habits/{hid}/streak")
    assert r.status_code == 200
    assert r.json() == {"habit_id": hid, "streak": 2}
