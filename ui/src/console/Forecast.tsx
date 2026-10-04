import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { api } from "../data/api";
import { useReplay } from "../data/replay";
import { EmptyState, ErrorState, Panel, Reading, Skeleton, StatusBadge } from "../design/data";
import { fmt, fmtDate } from "../design/format";
import { Table } from "../design/Table";
import { TimeSeriesChart } from "../design/TimeSeriesChart";
import { eventWindows, ReplayControls } from "./Overview";

const MODEL: Record<string, string> = {
  seasonal_naive: "Seasonal naive (yesterday)", weekly_naive: "Weekly naive", xgboost_quantile: "XGBoost quantile",
  chronos2: "Chronos-2, zero-shot", chronos_bolt: "Chronos-Bolt, zero-shot",
};

export default function Forecast() {
  const { dt, day, dayError } = useReplay();
  const meta = useQuery({ queryKey: ["meta"], queryFn: api.meta });
  const demand = useMemo(() => day && ({
    series: [
      { key: "actual", label: "Actual unmanaged demand", values: day.blocks.map((b) => b.demand_kw - b.pv_kw), color: "--ink", width: 1.5 },
      { key: "p50", label: "Forecast P50", values: day.blocks.map((b) => b.forecast_p50_kw), color: "--series-net", width: 2 },
      { key: "alloc", label: "Supply allocation", values: day.blocks.map((b) => b.allocation_kw), color: "--ink-faint", width: 1.5, step: true },
    ],
    band: { lo: day.blocks.map((b) => b.forecast_p10_kw), hi: day.blocks.map((b) => b.forecast_p90_kw), label: "Forecast P10–P90" },
    windows: eventWindows(day.blocks),
  }), [day]);
  const deficit = useMemo(() => day && ({
    series: [
      { key: "p50", label: "Deficit P50", values: day.blocks.map((b) => b.deficit_p50_kw), color: "--series-net", width: 2 },
      { key: "actual", label: "Actual deficit", values: day.blocks.map((b) => (b.allocation_kw != null ? Math.max(0, b.demand_kw - b.pv_kw - b.allocation_kw) : 0)), color: "--series-baseline", width: 2 },
    ],
    band: { lo: day.blocks.map(() => 0), hi: day.blocks.map((b) => b.deficit_p90_kw), label: "Deficit up to P90" },
    windows: eventWindows(day.blocks),
  }), [day]);

  if (dayError) return <ErrorState title="Forecast did not load" body={dayError.message} />;
  if (!day || !dt) return <Skeleton className="h-96" />;
  const fc = day.forecast;
  const acc = meta.data?.forecast?.accuracy?.[dt.scenario] as Record<string, any> | undefined;
  const dv = meta.data?.forecast?.decision_value?.[dt.scenario] as Record<string, any> | undefined;
  const socs = day.blocks.map((b) => b.battery_soc_pct ?? 0);
  const chargeBlocks = day.blocks.filter((b) => b.battery_kw < -0.05);

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-lg">Day-ahead forecast, {dt.id}</h1>
        <p className="text-sm text-muted">Issued at 00:00 for {fmtDate(day.date)} using {MODEL[fc.model ?? ""] ?? "no model"}. Quantiles of unmanaged demand, turned into a deficit forecast with the shortfall-risk model.</p>
      </div>
      <ReplayControls />
      {!fc.available ? (
        <EmptyState title="No forecast for this day" body="Forecasts start on day 28 of the year, after four weeks of history. Choose a later replay day." />
      ) : (
        <>
          <div className="grid gap-4 xl:grid-cols-[minmax(0,2fr)_minmax(280px,1fr)]">
            <Panel title="Deficit forecast, next 24 hours">
              <div className="p-4">
                {deficit && <TimeSeriesChart {...deficit} yLabel="Deficit" height={240}
                  summary={`Forecast deficit for ${fmtDate(day.date)}: evening P50 ${fmt.kwh(fc.evening_deficit_kwh?.["0.5"])}, P90 ${fmt.kwh(fc.evening_deficit_kwh?.["0.9"])}.`} />}
              </div>
            </Panel>
            <Panel title="What we'll do">
              <div className="flex flex-col gap-4 p-4">
                <div className="grid grid-cols-3 gap-3">
                  <Reading label="Evening deficit P50" value={fmt.num1(fc.evening_deficit_kwh?.["0.5"])} unit="kWh" />
                  <Reading label="P90" value={fmt.num1(fc.evening_deficit_kwh?.["0.9"])} unit="kWh" />
                  <Reading label="P99.5" value={fmt.num1(fc.evening_deficit_kwh?.["0.995"])} unit="kWh" />
                </div>
                <ol className="flex flex-col gap-2">
                  {(fc.plan ?? []).map((s, i) => (
                    <li key={i} className="grid grid-cols-[20px_1fr] gap-2 text-sm">
                      <span className="num text-muted">{i + 1}.</span>
                      <span><b className="font-semibold">{s.step}</b><br /><span className="text-muted">{s.detail}</span></span>
                    </li>
                  ))}
                </ol>
                <p className="text-sm text-muted">
                  Battery today: {chargeBlocks.length ? `charged in ${chargeBlocks.length} blocks between ${chargeBlocks[0].time} and ${chargeBlocks[chargeBlocks.length - 1].time} IST` : "no charging needed"}; lowest charge {fmt.pct(Math.min(...socs))}.
                </p>
              </div>
            </Panel>
          </div>
          <Panel title="Unmanaged demand against forecast">
            <div className="p-4">
              {demand && <TimeSeriesChart {...demand} yLabel="Power" height={240}
                summary={`Unmanaged demand and its day-ahead forecast for ${fmtDate(day.date)}.`} />}
            </div>
          </Panel>
        </>
      )}

      <div className="grid gap-4 xl:grid-cols-2">
        <Panel title="Accuracy over the test year (simulated DT)">
          {acc ? (
            <Table caption="Forecast accuracy by model" density="compact" data={Object.entries(acc).map(([k, v]) => ({ model: k, ...v }))}
              columns={[
                { header: "Model", accessorKey: "model", cell: (c) => MODEL[c.getValue() as string] ?? c.getValue() },
                { header: "MASE", accessorKey: "mase", cell: (c) => (c.getValue() as number).toFixed(2), meta: { align: "right" } },
                { header: "MAE", accessorKey: "mae_kw", cell: (c) => fmt.kw(c.getValue() as number), meta: { align: "right" } },
                { header: "P10–P90 coverage", accessorKey: "coverage_p10_p90", cell: (c) => (c.getValue() == null ? "–" : fmt.frac(c.getValue() as number)), meta: { align: "right" } },
              ]} />
          ) : <div className="p-4"><Skeleton className="h-24" /></div>}
          <p className="px-4 pb-3 pt-2 text-xs text-muted">MASE below 1 beats repeating yesterday's profile. A well-calibrated P10–P90 band covers 80% of blocks.</p>
        </Panel>
        <Panel title="Value of the forecast for the battery reserve">
          {dv ? (
            <Table caption="Reserve policy comparison" density="compact"
              data={Object.entries(dv).map(([k, v]) => ({ policy: k, ...v }))}
              columns={[
                { header: "Reserve policy", accessorKey: "policy", cell: (c) => {
                  let s = c.getValue() as string;
                  Object.entries(MODEL).forEach(([k, m]) => (s = s.replace(k, m)));
                  return <span className="whitespace-normal">{s}</span>;
                } },
                { header: "Availability", accessorKey: "essential_supply_availability", cell: (c) => `${((c.getValue() as number) * 100).toFixed(1)}%`, meta: { align: "right" } },
                { header: "Outage h", accessorKey: "outage_hours_per_home", cell: (c) => fmt.num1(c.getValue() as number), meta: { align: "right" } },
                { header: "Peak shaved", accessorKey: "peak_shaving_kwh", cell: (c) => `${((c.getValue() as number) / 1000).toFixed(1)} MWh`, meta: { align: "right" } },
              ]} maxHeight={360} />
          ) : <div className="p-4"><Skeleton className="h-24" /></div>}
          <div className="px-4 pb-3 pt-2"><StatusBadge status="ok" label="Year-long simulation, mean of 5 seeds" /></div>
        </Panel>
      </div>
    </div>
  );
}
