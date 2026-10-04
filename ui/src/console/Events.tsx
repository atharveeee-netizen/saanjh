import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../data/api";
import { useReplay } from "../data/replay";
import { EmptyState, ErrorState, Panel, Reading, Skeleton, StatusBadge } from "../design/data";
import { fmt, fmtDate, monthName } from "../design/format";
import { SegmentedControl } from "../design/primitives";
import { Table } from "../design/Table";

export default function Events() {
  const { dt } = useReplay();
  const nav = useNavigate();
  const q = useQuery({ queryKey: ["events", dt?.id], queryFn: () => api.events(dt!.id), enabled: !!dt });
  const [month, setMonth] = useState("all");
  const [search, setSearch] = useState("");
  const rows = useMemo(() => (q.data ?? []).filter((e) =>
    (month === "all" || Number(e.date.slice(5, 7)) === Number(month)) &&
    (!search || e.id.toLowerCase().includes(search.toLowerCase()) || e.date.includes(search))), [q.data, month, search]);
  if (q.error) return <ErrorState title="Events did not load" body={(q.error as Error).message} onRetry={() => q.refetch()} />;
  if (q.isLoading || !dt) return <Skeleton className="h-96" />;
  const all = q.data ?? [];
  const avoided = all.reduce((s, e) => s + e.mv.outage_minutes_avoided, 0);
  const months = Array.from(new Set(all.map((e) => Number(e.date.slice(5, 7))))).sort((a, b) => a - b);
  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-lg">Shortfall events, {dt.id}</h1>
        <p className="text-sm text-muted">Every supply shortfall in the simulated year, with what SAANJH did and the verified result against today's load shedding.</p>
      </div>
      <Panel>
        <div className="grid grid-cols-2 gap-4 p-4 md:grid-cols-4">
          <Reading label="Events this year" value={fmt.int(all.length)} />
          <Reading label="Hours under shortfall" value={fmt.num1(all.reduce((s, e) => s + e.duration_min, 0) / 60)} unit="h" />
          <Reading label="Household outage hours avoided" value={fmt.int(avoided / 60)} unit="h" />
          <Reading label="Events that needed disconnections" value={fmt.int(all.filter((e) => e.plan.homes_shed_max > 0).length)}
            status={all.some((e) => e.plan.homes_shed_max > 0) ? "warn" : "ok"} />
        </div>
      </Panel>
      <Panel title="All events" actions={
        <div className="flex flex-wrap items-center gap-2">
          <label className="relative" htmlFor="global-search">
            <span className="sr-only">Search events</span>
            <Search size={14} className="absolute left-2.5 top-2.5 text-muted" aria-hidden />
            <input id="global-search" placeholder="Search by ID or date (/)" value={search} onChange={(e) => setSearch(e.target.value)}
              className="h-8 w-56 rounded-ctl border border-rule bg-raised pl-8 pr-2 text-sm" />
          </label>
          <SegmentedControl label="Month" value={month} onValueChange={setMonth}
            options={[{ value: "all", label: "All" }, ...months.slice(-4).map((m) => ({ value: String(m), label: monthName(m) }))]} />
        </div>}>
        {rows.length ? (
          <Table caption="Shortfall events" data={rows} onRowClick={(e) => nav(`/events/${e.id}`)} maxHeight={640}
            columns={[
              { header: "Event", accessorKey: "id" },
              { header: "Date", accessorKey: "date", cell: (c) => fmtDate(c.getValue() as string) },
              { header: "Window (IST)", id: "win", accessorFn: (e) => `${e.start}–${e.end}` },
              { header: "Peak gap", accessorKey: "peak_gap_kw", cell: (c) => fmt.kw(c.getValue() as number), meta: { align: "right" } },
              { header: "Battery", id: "batt", accessorFn: (e) => e.plan.battery_kwh, cell: (c) => fmt.kwh(c.getValue() as number), meta: { align: "right" } },
              { header: "Lowest band", id: "band", accessorFn: (e) => e.plan.lowest_band_w ?? 0, cell: (c) => (c.getValue() ? fmt.watts(c.getValue() as number) : "Not needed") },
              { header: "Homes off (max)", id: "shed", accessorFn: (e) => e.plan.homes_shed_max, meta: { align: "right" } },
              { header: "Outage avoided", id: "avoided", accessorFn: (e) => e.mv.outage_minutes_avoided / 60, cell: (c) => fmt.hours(c.getValue() as number), meta: { align: "right" } },
              { header: "Status", accessorKey: "status", cell: (c) => {
                const s = c.getValue() as string;
                return <StatusBadge status={s === "cancelled" ? "offline" : "ok"} label={s === "verified" ? "Verified" : s === "approved" ? "Approved" : s === "cancelled" ? "Cancelled" : "Planned"} />;
              } },
            ]} />
        ) : <div className="p-4"><EmptyState title="No events match" body="Clear the search or choose All months." /></div>}
      </Panel>
    </div>
  );
}
