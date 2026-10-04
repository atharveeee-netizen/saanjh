import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../data/api";
import { useReplay } from "../data/replay";
import { ErrorState, Panel, Reading, Skeleton } from "../design/data";
import { fmt, monthName } from "../design/format";
import { Tabs } from "../design/primitives";
import { Table } from "../design/Table";

/** Grouped monthly columns: two series, 2px gap, rounded data ends, values in the tooltip. */
function MonthlyBars({ months, a, b, labelA, labelB, unit, summary }:
  { months: number[]; a: number[]; b: number[]; labelA: string; labelB: string; unit: string; summary: string }) {
  const W = 720, H = 220, L = 44, B = 24, T = 10;
  const max = Math.max(1, ...a, ...b);
  const step = (W - L - 8) / months.length;
  const bw = Math.min(18, (step - 10) / 2);
  const y = (v: number) => T + (H - T - B) * (1 - v / max);
  const ticks = [0, max / 2, max];
  return (
    <figure className="m-0">
      <div className="overflow-x-auto">
        <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full min-w-[520px]" role="img" aria-label={summary}>
          {ticks.map((t) => (
            <g key={t}>
              <line x1={L} x2={W} y1={y(t)} y2={y(t)} stroke="var(--chart-grid)" strokeWidth={1} />
              <text x={L - 6} y={y(t) + 4} textAnchor="end" fontSize={11} fill="var(--ink-muted)">{Math.round(t)}</text>
            </g>
          ))}
          {months.map((m, i) => {
            const x = L + i * step + step / 2;
            const bar = (v: number, dx: number, color: string, label: string) => {
              const h = (H - T - B) * (v / max);
              const top = y(v), r = Math.min(4, h);
              return (
                <path d={`M${x + dx} ${H - B}V${top + r}q0 -${r} ${r} -${r}h${bw - 2 * r}q${r} 0 ${r} ${r}V${H - B}Z`} fill={color}>
                  <title>{`${monthName(m)}, ${label}: ${v.toFixed(1)} ${unit}`}</title>
                </path>
              );
            };
            return (
              <g key={m}>
                {bar(a[i], -bw - 1, "var(--series-baseline)", labelA)}
                {bar(b[i], 1, "var(--series-net)", labelB)}
                <text x={x} y={H - 8} textAnchor="middle" fontSize={11} fill="var(--ink-muted)">{monthName(m)}</text>
              </g>
            );
          })}
        </svg>
      </div>
      <figcaption className="mt-2 flex flex-wrap gap-4 text-xs text-muted">
        <span className="inline-flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-[2px] bg-[var(--series-baseline)]" />{labelA}</span>
        <span className="inline-flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-[2px] bg-[var(--series-net)]" />{labelB}</span>
        <span>Values in {unit}; hover a column for its value.</span>
      </figcaption>
    </figure>
  );
}

export default function Reports() {
  const { dt } = useReplay();
  const [tab, setTab] = useState("reliability");
  const rq = useQuery({ queryKey: ["report", dt?.id], queryFn: () => api.report(dt!.id), enabled: !!dt });
  const meta = useQuery({ queryKey: ["meta"], queryFn: api.meta });
  if (rq.error) return <ErrorState title="Report did not load" body={(rq.error as Error).message} />;
  if (!rq.data || !meta.data || !dt) return <Skeleton className="h-96" />;
  const r = rq.data;
  const ann = meta.data.annual?.scenarios?.[dt.scenario];
  const eco = meta.data.economics?.scenarios?.[dt.scenario]?.reliability_only;
  const months = r.months.map((m) => m.month);
  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-lg">Reports, {dt.id}, {r.year}</h1>
        <p className="text-sm text-muted">{r.label}. Annual figures are the mean of {meta.data.annual?.seeds} simulated years; monthly figures are one simulated year.</p>
      </div>
      {ann && (
        <Panel title="Year at a glance">
          <div className="grid grid-cols-2 gap-4 p-4 md:grid-cols-4">
            <Reading label="Essential supply in deficit windows" value={fmt.frac(ann.saanjh.essential_supply_availability.mean)}
              delta={`Baseline ${fmt.frac(ann.baseline.essential_supply_availability.mean)}`} />
            <Reading label="Outage hours per home" value={fmt.num1(ann.saanjh.outage_hours_per_home.mean)} unit="h"
              delta={`Baseline ${fmt.hours(ann.baseline.outage_hours_per_home.mean)}`} />
            <Reading label="Household-hours preserved" value={fmt.int(ann.essential_household_hours_preserved.mean)} unit="h" />
            <Reading label="Demand flexibility for DFPO" value={fmt.num1(ann.saanjh.flexibility.demand_flexibility_mwh.mean)} unit="MWh"
              delta={`+ ${fmt.num1(ann.saanjh.flexibility.community_battery_kwh.mean / 1000)} MWh from the battery`} />
          </div>
        </Panel>
      )}
      <Panel>
        <div className="p-4">
          <Tabs label="Report" value={tab} onValueChange={setTab} items={[
            { value: "reliability", label: "Monthly reliability", content: (
              <div className="flex flex-col gap-4">
                <MonthlyBars months={months} a={r.months.map((m) => m.baseline_outage_hours_per_home)} b={r.months.map((m) => m.saanjh_outage_hours_per_home)}
                  labelA="Baseline outage hours per home" labelB="SAANJH outage hours per home" unit="h"
                  summary="Outage hours per home each month, baseline against SAANJH." />
                <Table caption="Monthly reliability" density="compact" data={r.months} maxHeight={420}
                  columns={[
                    { header: "Month", accessorKey: "month", cell: (c) => monthName(c.getValue() as number) },
                    { header: "Shortfall hours", accessorKey: "deficit_hours", meta: { align: "right" }, cell: (c) => fmt.num1(c.getValue() as number) },
                    { header: "Outage h/home, baseline", accessorKey: "baseline_outage_hours_per_home", meta: { align: "right" }, cell: (c) => fmt.num1(c.getValue() as number) },
                    { header: "Outage h/home, SAANJH", accessorKey: "saanjh_outage_hours_per_home", meta: { align: "right" }, cell: (c) => fmt.num1(c.getValue() as number) },
                    { header: "Home-hours on band", accessorKey: "banded_home_hours", meta: { align: "right" }, cell: (c) => fmt.int(c.getValue() as number) },
                  ]} />
              </div>) },
            { value: "dfpo", label: "Demand flexibility (DFPO)", content: (
              <div className="flex flex-col gap-4">
                <MonthlyBars months={months} a={r.months.map((m) => m.community_battery_kwh)} b={r.months.map((m) => m.demand_flexibility_kwh)}
                  labelA="Community battery (storage)" labelB="Demand flexibility (relays, appliances, band)" unit="kWh"
                  summary="Flexibility delivered each month." />
                <p className="max-w-prose text-sm text-muted">Demand flexibility is what homes stopped drawing from the grid during shortfalls: inverter relays, deferred appliances and energy capped by the essential band. Battery discharge is reported separately, because whether storage counts toward the Demand Flexibility Portfolio Obligation depends on the state regulation.</p>
              </div>) },
            { value: "economics", label: "Unit economics", content: eco ? (
              <dl className="grid max-w-xl grid-cols-[1fr_auto] gap-x-6 gap-y-2 text-base">
                <dt className="text-muted">Up-front cost (battery + edge)</dt><dd className="num m-0 text-right font-semibold">{fmt.rupees(eco.capex.total)}</dd>
                <dt className="text-muted">Annual DISCOM benefits</dt><dd className="num m-0 text-right font-semibold">{fmt.rupees(eco.annual.benefits_total)}</dd>
                <dt className="text-muted">Annual operating cost</dt><dd className="num m-0 text-right font-semibold">{fmt.rupees(eco.annual.opex_total)}</dd>
                <dt className="text-muted">Net cost per home per month</dt><dd className="num m-0 text-right font-semibold">{fmt.rupees(eco.net_cost_per_home_per_month)}</dd>
                <dt className="text-muted">Cost per household-hour preserved</dt><dd className="num m-0 text-right font-semibold">{fmt.rupees(eco.cost_per_household_hour_preserved)}</dd>
                <dt className="text-muted">A home inverter, per backup hour</dt><dd className="num m-0 text-right font-semibold">{fmt.rupees(eco.home_inverter_cost_per_backup_hour)}</dd>
                <dt className="text-muted">Up-front cost to a low-income home</dt><dd className="num m-0 text-right font-semibold">{fmt.rupees(eco.household.low_income_upfront)}</dd>
              </dl>) : <Skeleton className="h-40" /> },
          ]} />
        </div>
      </Panel>
      <p className="text-xs text-muted">To file this report on paper, use your browser's print command; the page prints on A4 without navigation.</p>
    </div>
  );
}
