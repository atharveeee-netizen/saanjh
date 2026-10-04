// Data access. Two modes with the same shapes:
//  * static (default): reads the JSON bundle in ./data/ (built by backend/export.py),
//    runs the replay clock in the browser and keeps operator actions in memory/localStorage.
//  * api: talks to the FastAPI service (backend/main.py). Enable with
//    localStorage "saanjh.api" = "http://localhost:8000" or VITE_API_URL at build time.

export interface DT {
  id: string; name: string; location_label: string; rating_kva: number; homes: number;
  homes_by_segment: Record<string, number>; lt_feeders: number; feeder_11kv: string;
  circle: string; division: string; subdivision: string; scenario: string; label: string;
}
export interface Block {
  t: number; time: string; demand_kw: number; pv_kw: number; allocation_kw: number | null; cut_pct: number;
  net_kw: number; baseline_net_kw: number; loading_pct: number; phase_a: [number, number, number];
  tail_voltage_v: number | null; baseline_tail_voltage_v: number | null; battery_kw: number;
  battery_soc_pct: number | null; relay_kw: number; appliance_kw: number; recharge_kw: number; rebound_kw: number;
  band_level_w: number | null; homes_banded: number; homes_shed: number; baseline_homes_shed: number;
  event_id: string | null; forecast_p10_kw: number | null; forecast_p50_kw: number | null;
  forecast_p90_kw: number | null; deficit_p50_kw: number | null; deficit_p90_kw: number | null;
}
export interface Day {
  dt_id: string; date: string; day_type: string; season: string; homes: number; label: string; blocks: Block[];
  forecast: { model: string | null; available: boolean; evening_deficit_kwh: Record<string, number> | null;
    plan: { step: string; detail: string }[] | null };
}
export interface DayInfo { date: string; day_type: string; season: string; deficit_kwh: number; featured: boolean; events: string[] }
export interface LogEntry { time: string; by: string; kind: "automatic" | "operator"; text: string }
export interface DEvent {
  id: string; dt_id: string; date: string; start: string; end: string; duration_min: number;
  status: string; peak_gap_kw: number;
  plan: { battery_kwh: number; relay_kwh: number; appliance_kwh: number; lowest_band_w: number | null;
    homes_banded_max: number; homes_shed_max: number };
  mv: { baseline_outage_home_minutes: number; saanjh_outage_home_minutes: number; outage_minutes_avoided: number;
    deficit_kwh: number; battery_kwh: number; dfpo_kwh: number; essential_supply_pct: number;
    baseline_essential_supply_pct: number };
  decision_log: LogEntry[];
}
export interface Household {
  id: string; segment: string; lt_feeder: number; phase: string; enrolment: string; flexibility: string;
  has_inverter: boolean; has_pv: boolean; critical: boolean; band_w: number; outage_hours_year: number;
  baseline_outage_hours_year: number; banded_hours_year: number; curtailment_minutes_year: number;
  battery_kwh_lent_year: number; credits_year_rs: number;
  consent: { recorded: boolean; method: string; language: string; label: string };
  profile?: number[]; profile_date?: string;
}
export interface Report {
  dt_id: string; year: number; label: string;
  months: { month: number; deficit_hours: number; baseline_outage_hours_per_home: number;
    saanjh_outage_hours_per_home: number; banded_home_hours: number; demand_flexibility_kwh: number;
    community_battery_kwh: number }[];
}

const API: string | null = (() => {
  try {
    return localStorage.getItem("saanjh.api") || (import.meta.env.VITE_API_URL as string) || null;
  } catch {
    return (import.meta.env.VITE_API_URL as string) || null;
  }
})();
export const mode = API ? "api" : "static";

const cache = new Map<string, Promise<any>>();
function staticJson<T>(path: string): Promise<T> {
  if (!cache.has(path)) {
    cache.set(path, fetch(`./data/${path}`).then((r) => {
      if (!r.ok) throw new Error(`Could not load ${path} (HTTP ${r.status}).`);
      return r.json();
    }));
  }
  return cache.get(path)!;
}
async function apiJson<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${API}${path}`, { headers: { "Content-Type": "application/json" }, ...init });
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || `Request failed (HTTP ${r.status}).`);
  return r.json();
}

/* ---------------- operator actions (static mode) */
const ACT_KEY = "saanjh.actions.v1";
type Action = { status: string; log: LogEntry };
function loadActions(): Record<string, Action[]> {
  try { return JSON.parse(localStorage.getItem(ACT_KEY) || "{}"); } catch { return {}; }
}
let actions = loadActions();
function saveActions() {
  try { localStorage.setItem(ACT_KEY, JSON.stringify(actions)); } catch { /* storage unavailable: keep in memory */ }
}
export function resetActions() { actions = {}; saveActions(); }

function withActions(ev: DEvent): DEvent {
  const a = actions[ev.id] || [];
  return { ...ev, status: a.length ? a[a.length - 1].status : ev.status, decision_log: [...ev.decision_log, ...a.map((x) => x.log)] };
}
function nowIst() {
  return new Date().toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", timeZone: "Asia/Kolkata" }) + " IST";
}

export const api = {
  meta: () => (API ? apiJson<any>("/api/meta") : staticJson<any>("meta.json")),
  dts: () => (API ? apiJson<DT[]>("/api/dts") : staticJson<DT[]>("dts.json")),
  days: (dt: string) => (API ? apiJson<DayInfo[]>(`/api/dts/${dt}/days`) : staticJson<DayInfo[]>(`dt_${dt}/days.json`)),
  day: async (dt: string, date: string): Promise<Day> => {
    if (API) {
      const ts = await apiJson<any>(`/api/dts/${dt}/timeseries?date=${date}`);
      const fc = await apiJson<any>(`/api/dts/${dt}/forecast?date=${date}`);
      const dts = await api.dts();
      return { ...ts, homes: dts.find((d) => d.id === dt)!.homes, season: "", forecast: fc };
    }
    return staticJson<Day>(`dt_${dt}/day_${date}.json`);
  },
  events: async (dt: string): Promise<DEvent[]> => {
    const list = API ? await apiJson<DEvent[]>(`/api/events?dt_id=${dt}&limit=1000`) : await staticJson<DEvent[]>(`dt_${dt}/events.json`);
    return API ? list : list.map(withActions);
  },
  event: async (dt: string, id: string): Promise<DEvent> => {
    if (API) return apiJson<DEvent>(`/api/events/${id}`);
    const ev = (await staticJson<DEvent[]>(`dt_${dt}/events.json`)).find((e) => e.id === id);
    if (!ev) throw new Error(`Event ${id} was not found for ${dt}.`);
    return withActions(ev);
  },
  act: async (dt: string, id: string, kind: "approve" | "modify" | "cancel", body: any = {}): Promise<DEvent> => {
    if (API) return apiJson<DEvent>(`/api/events/${id}/${kind}`, { method: "POST", body: JSON.stringify(body) });
    const ev = await api.event(dt, id);
    if (ev.status === "cancelled") throw new Error(`Event ${id} is cancelled; it can no longer be changed.`);
    const by = "SDO duty engineer";
    const text = kind === "approve" ? "Plan approved."
      : kind === "cancel" ? `Event cancelled.${body.note ? " " + body.note : ""}`
      : `Plan modified: ${[body.battery_reserve_kwh != null && `battery reserve set to ${body.battery_reserve_kwh} kWh`,
          body.band_floor_w != null && `band floor set to ${body.band_floor_w} W`].filter(Boolean).join(", ") || "no changes"}.`;
    (actions[id] ||= []).push({ status: kind === "cancel" ? "cancelled" : "approved", log: { time: nowIst(), by, kind: "operator", text } });
    saveActions();
    return withActions((await staticJson<DEvent[]>(`dt_${dt}/events.json`)).find((e) => e.id === id)!);
  },
  households: (dt: string) => (API ? apiJson<Household[]>(`/api/households?dt_id=${dt}`) : staticJson<Household[]>(`dt_${dt}/households.json`)),
  household: async (dt: string, id: string): Promise<Household> => {
    if (API) return apiJson<Household>(`/api/households/${id}`);
    const [rows, prof] = await Promise.all([staticJson<Household[]>(`dt_${dt}/households.json`),
      staticJson<any>(`dt_${dt}/household_profiles.json`)]);
    const h = rows.find((r) => r.id === id);
    if (!h) throw new Error(`Household ${id} was not found.`);
    return { ...h, profile: prof.homes[id], profile_date: prof.date };
  },
  bandByBlock: (dt: string) => staticJson<any>(`dt_${dt}/household_profiles.json`).then((p) => p.band_w_by_block as (number | null)[]),
  report: (dt: string) => (API ? apiJson<Report>(`/api/reports/monthly?dt_id=${dt}`) : staticJson<Report>(`dt_${dt}/reports.json`)),
  protocol: () => (API ? apiJson<any>("/api/protocol/samples") : staticJson<any>("protocol_samples.json")),
};

/** The event an operator or household cares about for a day: the first evening event
 *  (starting 17:00 or later), otherwise the day's first event. */
export function pickEvent(events: DEvent[], date: string | null | undefined): DEvent | undefined {
  const day = events.filter((e) => e.date === date);
  return day.find((e) => e.start >= "17:00") ?? day[0];
}
