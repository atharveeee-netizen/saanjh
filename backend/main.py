"""SAANJH API: serves simulation outputs in replay mode.

    uvicorn backend.main:app --reload --port 8000

A simulated clock walks through a chosen day, so the console behaves like a live control
room. Data comes from backend/data/ (built by ``python backend/export.py`` from the
simulation results). Every value is SIMULATED on inputs calibrated to real data; see
docs/DATA_SOURCES.md. Operator actions are kept in memory for the life of the process.
"""
import json
import os
import time
from datetime import datetime, timedelta
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
IST = "+05:30"


def _load(*parts):
    path = os.path.join(DATA, *parts)
    if not os.path.exists(path):
        raise HTTPException(404, f"No data at {'/'.join(parts)}. Run: python backend/export.py")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


app = FastAPI(
    title="SAANJH API",
    version="1.0.0",
    description="Essential-supply layer for distribution transformers. Replay of simulated operations.",
)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                   allow_methods=["*"], allow_headers=["*"])


# ----------------------------------------------------------------------------- models
class DT(BaseModel):
    id: str
    name: str
    location_label: str
    rating_kva: float
    homes: int
    homes_by_segment: dict[str, int]
    lt_feeders: int
    feeder_11kv: str
    circle: str
    division: str
    subdivision: str
    scenario: str
    label: str


class PhaseReading(BaseModel):
    r: float
    y: float
    b: float


class DTState(BaseModel):
    dt_id: str
    at: str
    block: int
    loading_pct: float
    net_kw: float
    phase_current_a: PhaseReading
    tail_voltage_v: Optional[float]
    battery_soc_pct: Optional[float]
    battery_kw: float = Field(description="+ discharge, - charge")
    homes_total: int
    homes_on_band: int
    homes_shed: int
    active_event_id: Optional[str]
    supply_limit_kw: Optional[float]
    data_age_min: int


class ClockSetting(BaseModel):
    dt_id: Optional[str] = None
    date: Optional[str] = None
    speed: float = Field(60.0, description="simulated minutes per real minute")
    start_time: str = "17:00"


class EventModify(BaseModel):
    battery_reserve_kwh: Optional[float] = None
    band_floor_w: Optional[Literal[300, 500, 750, 1000]] = None
    exclude_homes: list[str] = []
    note: str = ""


class OperatorNote(BaseModel):
    operator: str = "SDO duty engineer"
    note: str = ""


# ----------------------------------------------------------------------------- clock
_clock = {"dt_id": None, "date": None, "speed": 60.0, "start_time": "17:00", "set_at": time.time()}
_actions: dict[str, list] = {}


def _default_day(dt_id):
    days = _load(f"dt_{dt_id}", "days.json")
    return next((d["date"] for d in days if d.get("featured")), days[0]["date"])


def _replay_block(dt_id, at: Optional[str]):
    """Return (date, block index) for an explicit time or the running replay clock."""
    if at:
        try:
            ts = datetime.fromisoformat(at.replace("Z", ""))
        except ValueError:
            raise HTTPException(422, "at must be ISO 8601, e.g. 2023-10-26T18:30")
        return ts.date().isoformat(), (ts.hour * 60 + ts.minute) // 15
    date = _clock["date"] if _clock["dt_id"] == dt_id and _clock["date"] else _default_day(dt_id)
    h, m = map(int, _clock["start_time"].split(":"))
    elapsed = (time.time() - _clock["set_at"]) / 60 * _clock["speed"]
    minute = min(24 * 60 - 1, h * 60 + m + elapsed)
    return date, int(minute // 15)


def _iso(date, block):
    t = datetime.fromisoformat(date) + timedelta(minutes=15 * block)
    return t.strftime("%Y-%m-%dT%H:%M") + IST


# ----------------------------------------------------------------------------- routes
@app.get("/api/meta")
def meta():
    return _load("meta.json")


@app.get("/api/dts", response_model=list[DT])
def list_dts():
    return _load("dts.json")


@app.get("/api/dts/{dt_id}", response_model=DT)
def get_dt(dt_id: str):
    for d in _load("dts.json"):
        if d["id"] == dt_id:
            return d
    raise HTTPException(404, f"Unknown DT {dt_id}")


@app.get("/api/dts/{dt_id}/days")
def list_days(dt_id: str):
    return _load(f"dt_{dt_id}", "days.json")


@app.get("/api/dts/{dt_id}/state", response_model=DTState)
def dt_state(dt_id: str, at: Optional[str] = Query(None, description="ISO time; default = replay clock")):
    get_dt(dt_id)
    date, block = _replay_block(dt_id, at)
    day = _load(f"dt_{dt_id}", f"day_{date}.json")
    b = day["blocks"][block]
    return DTState(
        dt_id=dt_id, at=_iso(date, block), block=block, loading_pct=b["loading_pct"], net_kw=b["net_kw"],
        phase_current_a=PhaseReading(r=b["phase_a"][0], y=b["phase_a"][1], b=b["phase_a"][2]),
        tail_voltage_v=b.get("tail_voltage_v"), battery_soc_pct=b.get("battery_soc_pct"),
        battery_kw=b["battery_kw"], homes_total=day["homes"], homes_on_band=b["homes_banded"],
        homes_shed=b["homes_shed"], active_event_id=b.get("event_id"),
        supply_limit_kw=b.get("allocation_kw"), data_age_min=3)


@app.get("/api/dts/{dt_id}/timeseries")
def timeseries(dt_id: str, date: Optional[str] = None, from_: Optional[int] = Query(None, alias="from"),
               to: Optional[int] = None):
    """Per-block series for a replay day. ``from``/``to`` are block indices (0-95)."""
    get_dt(dt_id)
    day = _load(f"dt_{dt_id}", f"day_{date or _default_day(dt_id)}.json")
    blocks = day["blocks"][from_ or 0:(to + 1) if to is not None else None]
    return {"dt_id": dt_id, "date": day["date"], "day_type": day["day_type"], "label": day["label"], "blocks": blocks}


@app.get("/api/dts/{dt_id}/forecast")
def forecast(dt_id: str, date: Optional[str] = None):
    get_dt(dt_id)
    day = _load(f"dt_{dt_id}", f"day_{date or _default_day(dt_id)}.json")
    return {"dt_id": dt_id, "date": day["date"], **day["forecast"]}


@app.get("/api/events")
def list_events(dt_id: Optional[str] = None, date: Optional[str] = None, limit: int = 200):
    dts = [dt_id] if dt_id else [d["id"] for d in _load("dts.json")]
    out = []
    for d in dts:
        for ev in _load(f"dt_{d}", "events.json"):
            if date and ev["date"] != date:
                continue
            out.append({k: v for k, v in ev.items() if k not in ("decision_log",)} |
                       {"status": _status(ev)})
    return out[:limit]


def _status(ev):
    acts = _actions.get(ev["id"], [])
    return acts[-1]["status"] if acts else ev["status"]


def _find_event(event_id):
    for d in _load("dts.json"):
        for ev in _load(f"dt_{d['id']}", "events.json"):
            if ev["id"] == event_id:
                return ev
    raise HTTPException(404, f"Unknown event {event_id}")


@app.get("/api/events/{event_id}")
def get_event(event_id: str):
    ev = _find_event(event_id)
    log = ev["decision_log"] + [a["log"] for a in _actions.get(event_id, [])]
    return ev | {"status": _status(ev), "decision_log": log}


def _act(event_id, status, text, operator):
    ev = _find_event(event_id)
    if _status(ev) == "cancelled":
        raise HTTPException(409, f"Event {event_id} is {_status(ev)}; it can no longer be changed.")
    entry = {"status": status, "log": {"time": datetime.now().strftime("%H:%M") + " IST", "by": operator,
                                        "kind": "operator", "text": text}}
    _actions.setdefault(event_id, []).append(entry)
    return get_event(event_id)


@app.post("/api/events/{event_id}/approve")
def approve(event_id: str, body: OperatorNote = OperatorNote()):
    return _act(event_id, "approved", f"Plan approved. {body.note}".strip(), body.operator)


@app.post("/api/events/{event_id}/modify")
def modify(event_id: str, body: EventModify):
    parts = []
    if body.battery_reserve_kwh is not None:
        parts.append(f"battery reserve set to {body.battery_reserve_kwh:.0f} kWh")
    if body.band_floor_w is not None:
        parts.append(f"band floor set to {body.band_floor_w} W")
    if body.exclude_homes:
        parts.append(f"{len(body.exclude_homes)} homes excluded from banding")
    text = "Plan modified: " + (", ".join(parts) if parts else "no changes") + (f". {body.note}" if body.note else ".")
    return _act(event_id, "approved", text, "SDO duty engineer")


@app.post("/api/events/{event_id}/cancel")
def cancel(event_id: str, body: OperatorNote = OperatorNote()):
    return _act(event_id, "cancelled", f"Event cancelled. {body.note}".strip(), body.operator)


@app.get("/api/households")
def households(dt_id: str, segment: Optional[str] = None, q: Optional[str] = None):
    rows = _load(f"dt_{dt_id}", "households.json")
    if segment:
        rows = [r for r in rows if r["segment"] == segment]
    if q:
        rows = [r for r in rows if q.lower() in r["id"].lower()]
    return rows


@app.get("/api/households/{household_id}")
def household(household_id: str):
    dt_num = household_id.split("-")[1]
    dt_id = f"DT-{dt_num}"
    for r in _load(f"dt_{dt_id}", "households.json"):
        if r["id"] == household_id:
            profiles = _load(f"dt_{dt_id}", "household_profiles.json")
            return r | {"profile": profiles["homes"].get(household_id), "profile_date": profiles["date"]}
    raise HTTPException(404, f"Unknown household {household_id}")


@app.get("/api/reports/monthly")
def monthly_report(dt_id: str):
    return _load(f"dt_{dt_id}", "reports.json")


@app.get("/api/protocol/samples")
def protocol_samples():
    return _load("protocol_samples.json")


@app.post("/api/sim/clock")
def set_clock(body: ClockSetting):
    _clock.update({k: v for k, v in body.model_dump().items() if v is not None})
    _clock["set_at"] = time.time()
    return {k: v for k, v in _clock.items() if k != "set_at"}


@app.get("/api/sim/clock")
def get_clock():
    return {k: v for k, v in _clock.items() if k != "set_at"}
