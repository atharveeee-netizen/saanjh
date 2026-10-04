"""Every API endpoint answers with the documented shape (backend/main.py)."""
import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


@pytest.fixture(scope="module")
def dt_id():
    r = client.get("/api/dts")
    assert r.status_code == 200 and r.json()
    return r.json()[0]["id"]


@pytest.fixture(scope="module")
def event(dt_id):
    evs = client.get("/api/events", params={"dt_id": dt_id}).json()
    assert evs
    return evs[0]


def test_meta():
    assert "annual" in client.get("/api/meta").json()


def test_dt_detail(dt_id):
    d = client.get(f"/api/dts/{dt_id}").json()
    assert d["id"] == dt_id and d["rating_kva"] > 0
    assert client.get("/api/dts/DT-9999").status_code == 404


def test_state(dt_id):
    days = client.get(f"/api/dts/{dt_id}/days").json()
    s = client.get(f"/api/dts/{dt_id}/state", params={"at": f"{days[0]['date']}T18:30"}).json()
    assert s["block"] == 74 and len([s["phase_current_a"][k] for k in "ryb"]) == 3
    assert s["at"].endswith("+05:30")
    assert client.get(f"/api/dts/{dt_id}/state").status_code == 200   # replay clock


def test_timeseries_and_forecast(dt_id):
    ts = client.get(f"/api/dts/{dt_id}/timeseries", params={"from": 68, "to": 71}).json()
    assert len(ts["blocks"]) == 4
    fc = client.get(f"/api/dts/{dt_id}/forecast").json()
    assert "evening_deficit_kwh" in fc


def test_events_and_actions(event):
    eid = event["id"]
    detail = client.get(f"/api/events/{eid}").json()
    assert detail["decision_log"] and "mv" in detail
    r = client.post(f"/api/events/{eid}/approve", json={"operator": "test", "note": ""})
    assert r.status_code == 200 and r.json()["status"] == "approved"
    r = client.post(f"/api/events/{eid}/modify", json={"band_floor_w": 750})
    assert "band floor set to 750 W" in r.json()["decision_log"][-1]["text"]
    r = client.post(f"/api/events/{eid}/cancel", json={"operator": "test", "note": "supply restored"})
    assert r.json()["status"] == "cancelled"
    assert client.post(f"/api/events/{eid}/approve", json={}).status_code == 409


def test_households(dt_id):
    rows = client.get("/api/households", params={"dt_id": dt_id}).json()
    assert rows and rows[0]["id"].startswith("HH-")
    h = client.get(f"/api/households/{rows[0]['id']}").json()
    assert len(h["profile"]) == 96


def test_reports_protocol_clock(dt_id):
    rep = client.get("/api/reports/monthly", params={"dt_id": dt_id}).json()
    assert len(rep["months"]) == 12
    p = client.get("/api/protocol/samples").json()
    assert "openadr_event" in p and "ieee2030_5_dercontrol" in p
    c = client.post("/api/sim/clock", json={"dt_id": dt_id, "speed": 120, "start_time": "18:00"}).json()
    assert c["speed"] == 120 and client.get("/api/sim/clock").json()["start_time"] == "18:00"
