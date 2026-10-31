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


# ---------------------------------------------------------------------------
# Task 2: Validation tests
# ---------------------------------------------------------------------------


def test_create_habit_empty_name_rejected():
    """POST /habits with an empty name must return 422."""
    r = client.post("/habits", json={"name": ""})
    assert r.status_code == 422
    body = r.json()
    # Pydantic wraps errors under "detail"; check the message is meaningful
    assert "empty" in str(body).lower() or "whitespace" in str(body).lower()


def test_create_habit_whitespace_only_name_rejected():
    """POST /habits with a whitespace-only name must return 422."""
    r = client.post("/habits", json={"name": "   "})
    assert r.status_code == 422
    body = r.json()
    assert "empty" in str(body).lower() or "whitespace" in str(body).lower()


def test_create_habit_valid_name_accepted():
    """POST /habits with a normal name must still succeed."""
    r = client.post("/habits", json={"name": "Meditate"})
    assert r.status_code == 200
    assert r.json()["name"] == "Meditate"


def test_checkin_invalid_day_rejected():
    """POST /habits/{id}/checkin with a non-date 'day' must return 422."""
    hid = client.post("/habits", json={"name": "Run"}).json()["id"]
    r = client.post(f"/habits/{hid}/checkin", json={"day": "not-a-date"})
    assert r.status_code == 422
    body = r.json()
    assert "yyyy-mm-dd" in str(body).lower() or "valid date" in str(body).lower()


def test_checkin_wrong_format_day_rejected():
    """POST /habits/{id}/checkin with DD/MM/YYYY format must return 422."""
    hid = client.post("/habits", json={"name": "Yoga"}).json()["id"]
    r = client.post(f"/habits/{hid}/checkin", json={"day": "22/09/2026"})
    assert r.status_code == 422


def test_checkin_valid_day_accepted():
    """POST /habits/{id}/checkin with a correct YYYY-MM-DD date must succeed."""
    hid = client.post("/habits", json={"name": "Walk"}).json()["id"]
    r = client.post(f"/habits/{hid}/checkin", json={"day": "2026-10-01"})
    assert r.status_code == 200
    assert r.json()["day"] == "2026-10-01"
