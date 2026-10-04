import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import { useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../data/api";
import { useReplay } from "../data/replay";
import { ErrorState, Panel, Reading, Skeleton, StatusBadge, Stepper } from "../design/data";
import { fmt, fmtDate } from "../design/format";
import { Button, Dialog, TextField, useToast } from "../design/primitives";
import { TimeSeriesChart } from "../design/TimeSeriesChart";
import { ModifyPlanDialog } from "./ModifyPlanDialog";

const STEPS = ["Forecast", "Plan", "Approved", "Dispatching", "Completed", "Verified"];
const toBlock = (hhmm: string) => (hhmm === "24:00" ? 96 : Number(hhmm.slice(0, 2)) * 4 + Number(hhmm.slice(3)) / 15);

export default function EventDetail() {
  const { id = "" } = useParams();
  const { dt, days, date: replayDate, block } = useReplay();
  const nav = useNavigate();
  const qc = useQueryClient();
  const toast = useToast();
  const [modify, setModify] = useState(false);
  const [cancelOpen, setCancelOpen] = useState(false);
  const [reason, setReason] = useState("");
  const q = useQuery({ queryKey: ["event", id], queryFn: () => api.event(dt!.id, id), enabled: !!dt });
  const ev = q.data;
  const hasDay = !!ev && days.some((d) => d.date === ev.date);
  const dayQ = useQuery({ queryKey: ["day", dt?.id, ev?.date], queryFn: () => api.day(dt!.id, ev!.date), enabled: hasDay });
  const act = useMutation({
    mutationFn: (kind: "approve" | "cancel") => api.act(dt!.id, id, kind, kind === "cancel" ? { note: reason } : {}),
    onSuccess: (_d, kind) => {
      qc.invalidateQueries({ queryKey: ["event", id] }); qc.invalidateQueries({ queryKey: ["events"] });
      toast(kind === "approve" ? { title: "Plan approved", body: `${id} will run as planned.` }
        : { title: "Event cancelled", body: `${id} will not be dispatched. Normal supply rules apply.`, tone: "warn" });
      setCancelOpen(false);
    },
    onError: (e: Error) => toast({ title: "Action failed", body: e.message, tone: "alarm" }),
  });

  const chart = useMemo(() => {
    const d = dayQ.data;
    if (!d || !ev) return null;
    const from = Math.max(0, toBlock(ev.start) - 8), to = Math.min(95, toBlock(ev.end) + 8);
    const bl = d.blocks.slice(from, to + 1);
    return {
      series: [
        { key: "base", label: "Baseline: DT load after shedding", values: bl.map((b) => b.baseline_net_kw), color: "--series-baseline", width: 2 },
        { key: "net", label: "SAANJH: DT load", values: bl.map((b) => b.net_kw), color: "--series-net", width: 2 },
        { key: "alloc", label: "Supply allocation", values: bl.map((b) => b.allocation_kw), color: "--ink", width: 1.5, step: true },
        { key: "batt", label: "Community battery", values: bl.map((b) => Math.max(0, b.battery_kw)), color: "--series-battery", width: 1.5, fill: true },
      ],
      windows: [{ from: toBlock(ev.start) - from, to: toBlock(ev.end) - from, label: "Shortfall" }],
      offset: from,
    };
  }, [dayQ.data, ev]);

  if (q.error) return <ErrorState title="Event did not load" body={(q.error as Error).message} />;
  if (!ev || !dt) return <Skeleton className="h-96" />;

  // Workflow position. Past events are verified; on the replay day the clock decides.
  let step = 5;
  if (ev.status === "cancelled") step = 2;
  else if (ev.date === replayDate) {
    const s = toBlock(ev.start), e = toBlock(ev.end);
    step = block < s ? (ev.status === "approved" ? 2 : 1) : block < e ? 3 : block < e + 4 ? 4 : 5;
  }
  const hours = ev.duration_min / 60;
  const canAct = ev.status !== "cancelled" && step <= 2;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <Button variant="quiet" size="sm" icon={<ArrowLeft size={14} />} onClick={() => nav("/events")}>All events</Button>
          <h1 className="mt-1 text-lg">{ev.id}</h1>
          <p className="text-sm text-muted">{dt.name} · {fmtDate(ev.date)} · {ev.start}–{ev.end} IST · {ev.duration_min} min</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="primary" disabled={!canAct || ev.status === "approved"} loading={act.isPending && act.variables === "approve"}
            onClick={() => act.mutate("approve")}>{ev.status === "approved" ? "Plan approved" : "Approve plan"}</Button>
          <Button variant="secondary" disabled={!canAct} onClick={() => setModify(true)}>Modify plan</Button>
          <Button variant="destructive" disabled={!canAct} onClick={() => setCancelOpen(true)}>Cancel event</Button>
        </div>
      </div>
      {!canAct && ev.status !== "cancelled" && <p className="text-sm text-muted">This event has already been dispatched, so its plan can no longer be changed.</p>}

      <Panel><div className="p-4"><Stepper steps={STEPS} current={step} /></div></Panel>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Plan">
          <dl className="grid grid-cols-[1fr_auto] gap-x-6 gap-y-2 p-4 text-base">
            <dt className="text-muted">Gap at its peak</dt><dd className="num m-0 text-right font-semibold">{fmt.kw(ev.peak_gap_kw)}</dd>
            <dt className="text-muted">Community battery energy</dt><dd className="num m-0 text-right font-semibold">{fmt.kwh(ev.plan.battery_kwh)}</dd>
            <dt className="text-muted">Inverter relays, average</dt><dd className="num m-0 text-right font-semibold">{fmt.kw(ev.plan.relay_kwh / Math.max(hours, 0.25))}</dd>
            <dt className="text-muted">Appliance deferral, average</dt><dd className="num m-0 text-right font-semibold">{fmt.kw(ev.plan.appliance_kwh / Math.max(hours, 0.25))}</dd>
            <dt className="text-muted">Essential band</dt><dd className="num m-0 text-right font-semibold">{ev.plan.lowest_band_w ? `${fmt.watts(ev.plan.lowest_band_w)}, up to ${ev.plan.homes_banded_max} homes` : "Not needed"}</dd>
            <dt className="text-muted">Critical-load homes</dt><dd className="num m-0 text-right font-semibold">Keep 1,000 W band</dd>
            <dt className="text-muted">Disconnections</dt>
            <dd className="m-0 text-right"><StatusBadge status={ev.plan.homes_shed_max ? "warn" : "ok"} label={ev.plan.homes_shed_max ? `Up to ${ev.plan.homes_shed_max} homes, rotated` : "None"} /></dd>
          </dl>
        </Panel>
        <Panel title="Measurement and verification">
          <div className="grid grid-cols-2 gap-4 p-4">
            <Reading label="Essential supply, SAANJH" value={fmt.pct(ev.mv.essential_supply_pct)} status={ev.mv.essential_supply_pct >= 99 ? "ok" : "warn"} />
            <Reading label="Essential supply, baseline" value={fmt.pct(ev.mv.baseline_essential_supply_pct)} />
            <Reading label="Household outage time avoided" value={fmt.hours(ev.mv.outage_minutes_avoided / 60)} />
            <Reading label="Deficit energy" value={fmt.kwh(ev.mv.deficit_kwh)} />
            <Reading label="Served from community battery" value={fmt.kwh(ev.mv.battery_kwh)} />
            <Reading label="Counted toward DFPO" value={fmt.kwh(ev.mv.dfpo_kwh)} delta="relays + appliances + band" />
          </div>
        </Panel>
      </div>

      {chart ? (
        <Panel title="Baseline against actual">
          <div className="p-4">
            <TimeSeriesChart series={chart.series} windows={chart.windows} yLabel="Power" height={240}
              summary={`During ${ev.id}, baseline load shedding pulled the DT load below the allocation while SAANJH held it at the allocation and kept homes on.`} />
          </div>
        </Panel>
      ) : (
        <Panel title="Baseline against actual">
          <div className="grid gap-3 p-4 sm:grid-cols-2">
            {[["Baseline: household outage time", ev.mv.baseline_outage_home_minutes / 60, "var(--series-baseline)"],
              ["SAANJH: household outage time", ev.mv.saanjh_outage_home_minutes / 60, "var(--series-net)"]].map(([label, v, c]) => (
              <div key={label as string} className="flex flex-col gap-1">
                <span className="text-sm text-muted">{label as string}</span>
                <span className="flex items-center gap-2">
                  <span className="h-3 rounded-[2px]" style={{ background: c as string, width: `${Math.max(2, ((v as number) / Math.max(1, ev.mv.baseline_outage_home_minutes / 60)) * 100)}%` }} />
                  <span className="num whitespace-nowrap font-semibold">{fmt.hours(v as number)}</span>
                </span>
              </div>
            ))}
            <p className="text-xs text-muted sm:col-span-2">Per-block chart available for the replay days listed on the Overview.</p>
          </div>
        </Panel>
      )}

      <Panel title="Decision log">
        <ol className="divide-y divide-[var(--rule)]">
          {ev.decision_log.map((l, i) => (
            <li key={i} className="grid gap-1 px-4 py-3 sm:grid-cols-[96px_160px_1fr]">
              <span className="num text-sm font-semibold">{l.time}</span>
              <span className="text-sm text-muted">{l.by}</span>
              <span className="text-sm">{l.text}</span>
            </li>
          ))}
        </ol>
      </Panel>

      <ModifyPlanDialog open={modify} onOpenChange={setModify} event={ev} />
      <Dialog open={cancelOpen} onOpenChange={setCancelOpen} title={`Cancel ${ev.id}?`}
        description="The gateway will not dispatch this plan. If the shortfall happens, the DISCOM's own load shedding applies."
        footer={<>
          <Button variant="secondary" onClick={() => setCancelOpen(false)}>Keep event</Button>
          <Button variant="destructive" loading={act.isPending && act.variables === "cancel"} onClick={() => act.mutate("cancel")}>Cancel event</Button>
        </>}>
        <TextField id="cancel-reason" label="Reason (recorded in the log)" value={reason} onChange={(e) => setReason(e.target.value)} placeholder="e.g. Feeder under maintenance" />
      </Dialog>
    </div>
  );
}
