import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pause, Play, RotateCcw, SkipBack, SkipForward } from "lucide-react";
import { Fragment, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, Block, DEvent } from "../data/api";
import { useReplay } from "../data/replay";
import { EmptyState, ErrorState, Panel, PhaseReading, Reading, Skeleton, StatusBadge } from "../design/data";
import { blockTime, fmt, fmtDate } from "../design/format";
import { Button, Drawer, IconButton, Select, useToast } from "../design/primitives";
import { Table } from "../design/Table";
import { TimeSeriesChart } from "../design/TimeSeriesChart";
import { ModifyPlanDialog } from "./ModifyPlanDialog";
import { SingleLineDiagram, SldElement } from "./SingleLineDiagram";

export function eventWindows(blocks: Block[]) {
  const out: { from: number; to: number; label: string; id: string }[] = [];
  for (const b of blocks) {
    if (!b.event_id) continue;
    const last = out[out.length - 1];
    if (last && last.id === b.event_id && last.to === b.t) last.to = b.t + 1;
    else out.push({ from: b.t, to: b.t + 1, label: "Shortfall", id: b.event_id });
  }
  return out;
}

export function ReplayControls() {
  const { dts, dt, setDtId, days, date, setDate, block, setBlock, playing, setPlaying } = useReplay();
  return (
    <div className="no-print flex flex-wrap items-end gap-3">
      {dts.length > 1 && dt && (
        <Select id="dt-select" label="Transformer" value={dt.id} onValueChange={setDtId}
          options={dts.map((d) => ({ value: d.id, label: `${d.id} · ${d.location_label}` }))} />
      )}
      {date && (
        <Select id="day-select" label="Replay day (simulated)" value={date} onValueChange={setDate}
          options={days.map((d) => ({ value: d.date, label: `${fmtDate(d.date)} · ${d.day_type}${d.events.length ? ` · ${d.events.length} shortfall${d.events.length > 1 ? "s" : ""}` : " · no shortfall"}` }))} />
      )}
      <div className="flex items-center gap-1">
        <IconButton label="Back 15 minutes" onClick={() => setBlock(Math.max(0, block - 1))}><SkipBack size={16} /></IconButton>
        <Button size="sm" variant="secondary" icon={playing ? <Pause size={14} /> : <Play size={14} />} onClick={() => setPlaying(!playing)}>
          {playing ? "Pause replay" : "Play replay"}
        </Button>
        <IconButton label="Forward 15 minutes" onClick={() => setBlock(Math.min(95, block + 1))}><SkipForward size={16} /></IconButton>
      </div>
      <label className="flex min-w-[200px] flex-1 flex-col gap-1 text-sm font-semibold" htmlFor="replay-slider">
        Time of day: <span className="num font-normal text-muted">{blockTime(block)} IST</span>
        <input id="replay-slider" type="range" min={0} max={95} value={block} onChange={(e) => setBlock(Number(e.target.value))}
          className="accent-[var(--accent)]" />
      </label>
    </div>
  );
}

function NextWindow({ events }: { events: DEvent[] }) {
  const { dt, day, block } = useReplay();
  const qc = useQueryClient();
  const toast = useToast();
  const nav = useNavigate();
  const [modify, setModify] = useState(false);
  const todays = events.filter((e) => e.date === day?.date);
  const next = todays.find((e) => {
    const [h, m] = e.end === "24:00" ? [24, 0] : e.end.split(":").map(Number);
    return (h * 60 + m) / 15 > block;
  });
  const approve = useMutation({
    mutationFn: () => api.act(dt!.id, next!.id, "approve"),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["events"] }); toast({ title: "Plan approved", body: `${next!.id} will run as planned.` }); },
    onError: (e: Error) => toast({ title: "Could not approve the plan", body: e.message, tone: "alarm" }),
  });
  if (!day) return <Skeleton className="h-64" />;
  const fc = day.forecast;
  if (!next) {
    return (
      <Panel title="Next deficit window">
        <div className="p-4">
          <EmptyState title="No shortfall expected for the rest of this day"
            body={fc.evening_deficit_kwh ? `Forecast evening deficit: P90 ${fmt.kwh(fc.evening_deficit_kwh["0.9"])}. The community battery stays charged for the next window.` : "Choose another replay day to see a shortfall event."} />
        </div>
      </Panel>
    );
  }
  const win = day.blocks.filter((b) => b.event_id === next.id);
  const p50 = Math.max(0, ...win.map((b) => b.deficit_p50_kw ?? 0));
  const p90 = Math.max(0, ...win.map((b) => b.deficit_p90_kw ?? 0));
  const decided = next.status === "approved" || next.status === "cancelled";
  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === "a" && !decided && !(e.target as HTMLElement).closest("input,textarea")) { e.preventDefault(); approve.mutate(); }
  };
  return (
    <div onKeyDown={onKey} tabIndex={-1} className="outline-none">
    <Panel title="Next deficit window" actions={<StatusBadge status={next.status === "cancelled" ? "offline" : "warn"} label={next.status === "verified" ? "Plan ready" : next.status === "approved" ? "Plan approved" : next.status === "cancelled" ? "Cancelled" : "Plan ready"} />}>
      <div className="flex flex-col gap-4 p-4">
        <div>
          <p className="num text-xl font-semibold">{next.start}–{next.end} IST</p>
          <p className="text-sm text-muted">{fmtDate(next.date)} · {next.id}</p>
        </div>
        <div className="grid grid-cols-3 gap-3">
          <Reading label="Gap, forecast P50" value={fmt.num1(p50)} unit="kW" />
          <Reading label="Gap, forecast P90" value={fmt.num1(p90)} unit="kW" />
          <Reading label="Gap, measured peak" value={fmt.num1(next.peak_gap_kw)} unit="kW" />
        </div>
        <div>
          <h3 className="mb-2 text-sm font-semibold">Recommended plan</h3>
          <ol className="flex flex-col gap-2">
            {(fc.plan ?? []).map((s, i) => (
              <li key={i} className="grid grid-cols-[20px_1fr] gap-2 text-sm">
                <span className="num text-muted">{i + 1}.</span>
                <span><b className="font-semibold">{s.step}</b><br /><span className="text-muted">{s.detail}</span></span>
              </li>
            ))}
          </ol>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="primary" loading={approve.isPending} disabled={decided} onClick={() => approve.mutate()}
            data-shortcut="approve">{next.status === "approved" ? "Plan approved" : "Approve plan"}</Button>
          <Button variant="secondary" disabled={next.status === "cancelled"} onClick={() => setModify(true)}>Modify</Button>
          <Button variant="quiet" onClick={() => nav(`/events/${next.id}`)}>Open event</Button>
        </div>
        <ModifyPlanDialog open={modify} onOpenChange={setModify} event={next} />
        <p className="text-xs text-muted">Press <kbd className="font-cond">a</kbd> while this panel has focus to approve.</p>
      </div>
    </Panel>
    </div>
  );
}

function ElementDrawer({ el, onClose, b }: { el: SldElement | null; onClose: () => void; b: Block }) {
  const { dt } = useReplay();
  if (!el || !dt) return null;
  const titles: Record<string, string> = {
    incomer: `${dt.feeder_11kv} incomer`, dt: `${dt.id} transformer`, battery: "Community battery",
    gateway: "SAANJH gateway", feeder: `LT feeder ${el.kind === "feeder" ? el.index + 1 : ""}`,
  };
  const rows: [string, string][] =
    el.kind === "incomer" ? [["Supply limit", b.allocation_kw != null ? fmt.kw(b.allocation_kw) : "No limit"], ["Cut ordered", fmt.pct(b.cut_pct)], ["Breaker", "Closed"]]
    : el.kind === "dt" ? [["Loading", fmt.pct(b.loading_pct)], ["Net load", fmt.kw(b.net_kw)], ["Demand before PV", fmt.kw(b.demand_kw)], ["Rooftop PV", fmt.kw(b.pv_kw)], ["Tail-end voltage", fmt.volts(b.tail_voltage_v)], ["R / Y / B current", b.phase_a.map((a) => fmt.amps(a)).join(" / ")]]
    : el.kind === "battery" ? [["State of charge", fmt.pct(b.battery_soc_pct)], ["Power", b.battery_kw >= 0 ? `${fmt.kw(b.battery_kw)} out` : `${fmt.kw(-b.battery_kw)} in`]]
    : el.kind === "gateway" ? [["Backhaul", "Connected"], ["Plan", b.event_id ? `Running ${b.event_id}` : "Standby"], ["Inverter relays carrying", fmt.kw(b.relay_kw)], ["Appliances deferred", fmt.kw(b.appliance_kw)]]
    : [["Load", fmt.kw(((b as any).feeder_kw ?? [])[el.index])], ["Homes on band", String(((b as any).feeder_banded ?? [])[el.index] ?? 0)], ["Homes disconnected", String(((b as any).feeder_shed ?? [])[el.index] ?? 0)]];
  return (
    <Drawer open onOpenChange={(o) => !o && onClose()} title={titles[el.kind]} subtitle={`Readings at ${b.time} IST (simulated)`}>
      <dl className="grid grid-cols-[1fr_auto] gap-x-4 gap-y-2 text-base">
        {rows.map(([k, v]) => (
          <Fragment key={k}><dt className="text-muted">{k}</dt><dd className="num m-0 text-right font-semibold">{v}</dd></Fragment>
        ))}
      </dl>
    </Drawer>
  );
}

export default function Overview() {
  const { dt, day, block, dayLoading, dayError, staleMeter } = useReplay();
  const nav = useNavigate();
  const [sel, setSel] = useState<SldElement | null>(null);
  const [zoom, setZoom] = useState<[number, number] | null>(null);
  const evQ = useQuery({ queryKey: ["events", dt?.id], queryFn: () => api.events(dt!.id), enabled: !!dt });
  const hhQ = useQuery({ queryKey: ["households", dt?.id], queryFn: () => api.households(dt!.id), enabled: !!dt });

  const chart = useMemo(() => {
    if (!day) return null;
    const bl = zoom ? day.blocks.slice(zoom[0], zoom[1] + 1) : day.blocks;
    return {
      series: [
        { key: "demand", label: "Demand", values: bl.map((b) => b.demand_kw - b.pv_kw), color: "--ink-faint", width: 1.5, dash: [3, 3] },
        { key: "pv", label: "Rooftop PV", values: bl.map((b) => b.pv_kw), color: "--series-pv", width: 1.5 },
        { key: "alloc", label: "Supply allocation", values: bl.map((b) => b.allocation_kw), color: "--ink", width: 1.5, step: true },
        { key: "net", label: "DT load", values: bl.map((b) => b.net_kw), color: "--series-net", width: 2 },
      ],
      band: { lo: bl.map((b) => b.forecast_p10_kw), hi: bl.map((b) => b.forecast_p90_kw), label: "Forecast P10–P90" },
      windows: eventWindows(bl),
      now: zoom ? (block >= zoom[0] && block <= zoom[1] ? block - zoom[0] : undefined) : block,
    };
  }, [day, block, zoom]);

  if (dayError) return <ErrorState title="Replay data did not load" body={`${dayError.message} Run python backend/export.py to rebuild the data bundle.`} />;
  if (dayLoading || !day || !dt) {
    return (
      <div className="grid gap-4 xl:grid-cols-[2fr_1fr]" aria-busy="true">
        <Skeleton className="h-[420px]" /><Skeleton className="h-[420px]" />
        <Skeleton className="h-72 xl:col-span-2" /><Skeleton className="h-24 xl:col-span-2" />
      </div>
    );
  }
  const b = day.blocks[block];
  const homesTotal = day.homes;
  const st = b.loading_pct > 100 ? "alarm" : b.loading_pct > 90 ? "warn" : "ok";
  const vLow = (b.tail_voltage_v ?? 230) < 216.2;
  const logRows = (evQ.data ?? []).filter((e) => e.date === day.date)
    .flatMap((e) => e.decision_log.map((l) => ({ ...l, event: e.id, status: e.status })));
  const summary = `DT load, supply allocation and forecast for ${fmtDate(day.date)}. Peak DT load ${fmt.kw(Math.max(...day.blocks.map((x) => x.net_kw)))}; `
    + `${eventWindows(day.blocks).length} shortfall window(s).`;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-lg">{dt.name}</h1>
          <p className="text-sm text-muted">{dt.location_label} · {dt.homes} homes · {dt.feeder_11kv} · {day.label}</p>
        </div>
      </div>
      <ReplayControls />
      {staleMeter && (
        <ErrorState title="Meter data delayed" body={`Meter data for ${dt.id} hasn't arrived since ${blockTime(Math.max(0, block - 1))} IST. Showing the last known state; the gateway keeps running the approved plan.`} />
      )}

      <div className="grid items-start gap-4 xl:grid-cols-[minmax(0,2fr)_minmax(300px,1fr)]">
        <Panel title="Single-line diagram" actions={<StatusBadge status={st} label={st === "ok" ? "Within rating" : st === "warn" ? "High loading" : "Overloaded"} />}>
          <div className="p-3">
            <SingleLineDiagram dt={dt} block={b} homes={hhQ.data ?? []} onSelect={setSel} />
          </div>
        </Panel>
        <NextWindow events={evQ.data ?? []} />
      </div>

      <Panel title="Today, 24 hours" actions={zoom && <Button size="sm" variant="quiet" icon={<RotateCcw size={14} />} onClick={() => setZoom(null)}>Reset zoom</Button>}>
        <div className="p-4">
          {chart && <TimeSeriesChart {...chart} rating={{ value: dt.rating_kva * 0.95, label: `DT rating ${dt.rating_kva} kVA` }}
            yLabel="Power" summary={summary} onBrush={(a, z) => setZoom(zoom ? [zoom[0] + a, zoom[0] + z] : [a, z])} />}
          <p className="mt-1 text-xs text-muted">Drag across the chart to zoom. Select a time on the slider above to move the replay.</p>
        </div>
      </Panel>

      <Panel title="Readings">
        <div className="grid grid-cols-2 gap-4 p-4 sm:grid-cols-3 lg:grid-cols-6">
          <Reading label="DT loading" value={fmt.int(b.loading_pct)} unit="%" status={st} />
          <PhaseReading label="Phase current" values={b.phase_a} unit="A" />
          <Reading label="Tail-end voltage" value={fmt.int(b.tail_voltage_v)} unit="V" status={vLow ? "warn" : "ok"} />
          <Reading label="Community battery" value={fmt.int(b.battery_soc_pct)} unit="%"
            delta={b.battery_kw > 0.05 ? `${fmt.kw(b.battery_kw)} out` : b.battery_kw < -0.05 ? `${fmt.kw(-b.battery_kw)} in` : "Idle"} />
          <Reading label="Homes on essential band" value={`${b.homes_banded} of ${homesTotal}`} />
          <Reading label="Homes disconnected" value={b.homes_shed} status={b.homes_shed ? "alarm" : "ok"}
            delta={`Baseline today: ${b.baseline_homes_shed}`} />
        </div>
      </Panel>

      <Panel title="Event log" actions={<Button size="sm" variant="quiet" onClick={() => nav("/events")}>All events</Button>}>
        {logRows.length ? (
          <Table caption="Decisions logged today" data={logRows} density="compact" maxHeight={300}
            onRowClick={(r) => nav(`/events/${r.event}`)}
            columns={[
              { header: "Time", accessorKey: "time" },
              { header: "Event", accessorKey: "event" },
              { header: "Action", accessorKey: "text", cell: (c) => <span className="whitespace-normal">{c.getValue() as string}</span> },
              { header: "Outcome", accessorKey: "status", cell: (c) => <StatusBadge status={c.getValue() === "cancelled" ? "offline" : "ok"} label={String(c.getValue()).replace(/^./, (x) => x.toUpperCase())} /> },
              { header: "By", accessorKey: "by" },
            ]} />
        ) : <div className="p-4"><EmptyState title="Nothing logged yet today" body="Decisions appear here as soon as the gateway or an operator acts." /></div>}
      </Panel>
      <ElementDrawer el={sel} onClose={() => setSel(null)} b={b} />
    </div>
  );
}
