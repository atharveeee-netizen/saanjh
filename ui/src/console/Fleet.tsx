import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { useReplay } from "../data/replay";
import { EmptyState, ErrorState, Panel, Skeleton, Sparkline, StatusBadge } from "../design/data";
import { fmt, fmtDate } from "../design/format";
import { Button } from "../design/primitives";

interface FleetRow {
  dt_id: string; name: string; location_label: string; homes: number; rating_kva: number; segment_mix: string;
  risk_p90_kwh: number; risk_p50_kwh: number; p_any: number; forecast_p50: number[]; drillable: boolean;
  outage_hours_year: number;
}

export default function Fleet() {
  const { setDtId } = useReplay();
  const nav = useNavigate();
  const q = useQuery({ queryKey: ["fleet"], queryFn: () => fetch("./data/fleet.json").then((r) => {
    if (!r.ok) throw new Error("fleet.json is missing. Run python backend/export.py.");
    return r.json() as Promise<{ date: string; label: string; rows: FleetRow[] }>;
  }) });
  if (q.error) return <ErrorState title="Fleet view did not load" body={(q.error as Error).message} />;
  if (!q.data) return <Skeleton className="h-96" />;
  const rows = [...q.data.rows].sort((a, b) => b.risk_p90_kwh - a.risk_p90_kwh);
  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-lg">Transformers in Sub-division 4, ranked by tomorrow's deficit risk</h1>
        <p className="text-sm text-muted">Forecast for {fmtDate(q.data.date)}, issued at midnight. {q.data.label}</p>
      </div>
      <Panel>
        {rows.length ? (
          <ul className="divide-y divide-[var(--rule)]">
            {rows.map((r, i) => {
              const status = r.risk_p90_kwh > 40 ? "alarm" : r.risk_p90_kwh > 10 ? "warn" : "ok";
              return (
                <li key={r.dt_id} className="grid items-center gap-x-4 gap-y-2 px-4 py-3 md:grid-cols-[32px_minmax(180px,1.4fr)_120px_1fr_120px_140px]">
                  <span className="num text-sm text-muted">{i + 1}</span>
                  <span className="min-w-0">
                    <b className="font-semibold">{r.dt_id}</b> <span className="text-sm text-muted">· {r.rating_kva} kVA · {r.homes} homes</span><br />
                    <span className="text-sm text-muted">{r.location_label} · {r.segment_mix}</span>
                  </span>
                  <StatusBadge status={status} label={status === "alarm" ? "High risk" : status === "warn" ? "Some risk" : "Low risk"} />
                  <span className="flex items-center gap-3">
                    <Sparkline values={r.forecast_p50} label={`Forecast demand for ${r.dt_id}`} width={140} height={28} />
                    <span className="text-xs text-muted">P(shortfall) {fmt.frac(r.p_any)}</span>
                  </span>
                  <span className="num text-sm"><b>{fmt.num1(r.risk_p90_kwh)}</b> kWh<br /><span className="text-xs text-muted">P90 evening deficit</span></span>
                  {r.drillable
                    ? <Button size="sm" variant="secondary" onClick={() => { setDtId(r.dt_id); nav("/"); }}>Open {r.dt_id}</Button>
                    : <span className="text-xs text-muted">Forecast only in this demo</span>}
                </li>
              );
            })}
          </ul>
        ) : <div className="p-4"><EmptyState title="No transformers" body="Run the export to build the fleet list." /></div>}
      </Panel>
    </div>
  );
}
