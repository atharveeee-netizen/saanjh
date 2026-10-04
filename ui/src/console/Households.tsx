import { useQuery } from "@tanstack/react-query";
import { Copy, Search } from "lucide-react";
import { useMemo, useState } from "react";
import { api, Household } from "../data/api";
import { useReplay } from "../data/replay";
import { EmptyState, ErrorState, Panel, Reading, Skeleton, StatusBadge } from "../design/data";
import { fmt, fmtDate } from "../design/format";
import { Button, Drawer, SegmentedControl, Select, useToast } from "../design/primitives";
import { Density, Table } from "../design/Table";
import { TimeSeriesChart } from "../design/TimeSeriesChart";

function toCsv(rows: Household[]) {
  const cols: (keyof Household)[] = ["id", "segment", "lt_feeder", "phase", "enrolment", "flexibility", "critical", "band_w",
    "outage_hours_year", "baseline_outage_hours_year", "banded_hours_year", "battery_kwh_lent_year", "credits_year_rs"];
  return [cols.join(","), ...rows.map((r) => cols.map((c) => String(r[c])).join(","))].join("\n");
}

function HouseholdDrawer({ id, onClose }: { id: string | null; onClose: () => void }) {
  const { dt } = useReplay();
  const q = useQuery({ queryKey: ["household", id], queryFn: () => api.household(dt!.id, id!), enabled: !!id && !!dt });
  const bandQ = useQuery({ queryKey: ["band", dt?.id], queryFn: () => api.bandByBlock(dt!.id), enabled: !!dt });
  const h = q.data;
  const chart = useMemo(() => {
    if (!h?.profile || !bandQ.data) return null;
    const limit = bandQ.data.map((b) => (b == null ? null : (h.critical ? Math.max(b, 1000) : b) / 1000));
    return {
      series: [
        { key: "load", label: "Home demand", values: h.profile.map((w) => w / 1000), color: "--series-net", width: 2 },
        { key: "band", label: "Essential band in force", values: limit, color: "--status-warn", width: 1.5, step: true },
      ],
    };
  }, [h, bandQ.data]);
  return (
    <Drawer open={!!id} onOpenChange={(o) => !o && onClose()} title={id ?? ""} subtitle={h ? `${h.segment} home · LT-${h.lt_feeder}, phase ${h.phase}` : undefined}>
      {!h ? <Skeleton className="h-64" /> : (
        <div className="flex flex-col gap-5">
          <div className="grid grid-cols-2 gap-4">
            <Reading label="Outage hours this year" value={fmt.num1(h.outage_hours_year)} unit="h" delta={`Baseline: ${fmt.hours(h.baseline_outage_hours_year)}`} />
            <Reading label="Hours on essential band" value={fmt.num1(h.banded_hours_year)} unit="h" />
            <Reading label="Battery energy lent" value={fmt.num1(h.battery_kwh_lent_year)} unit="kWh" />
            <Reading label="Credits this year" value={fmt.rupees(h.credits_year_rs)} />
          </div>
          {chart && (
            <section>
              <h3 className="mb-2 text-sm font-semibold">Consumption against band, {h.profile_date ? fmtDate(h.profile_date) : ""}</h3>
              <TimeSeriesChart series={chart.series} yLabel="Power" height={180}
                summary="Home demand through the day with the essential band level shown when it was in force." />
              <p className="mt-1 text-xs text-muted">The band only limits a home whose draw is above it. Lights, fans, fridge and phone charging fit inside 500 W.</p>
            </section>
          )}
          <section className="flex flex-col gap-2 text-sm">
            <h3 className="font-semibold">Enrolment and consent</h3>
            <dl className="grid grid-cols-[140px_1fr] gap-y-1">
              <dt className="text-muted">Status</dt><dd className="m-0">{h.enrolment}</dd>
              <dt className="text-muted">Flexibility</dt><dd className="m-0">{h.flexibility}</dd>
              <dt className="text-muted">Band</dt><dd className="m-0">{fmt.watts(h.band_w)}{h.critical ? " (critical load)" : ""}</dd>
              <dt className="text-muted">Consent</dt><dd className="m-0">{h.consent.recorded ? `${h.consent.method}, in ${h.consent.language}` : "Not recorded (opted out)"}</dd>
              <dt className="text-muted">Opt-out history</dt><dd className="m-0">{h.enrolment === "opted out" ? "Opted out by SMS reply STOP; honoured from the next event" : "None"}</dd>
            </dl>
            <p className="text-xs text-faint">{h.consent.label}</p>
          </section>
        </div>
      )}
    </Drawer>
  );
}

export default function Households() {
  const { dt } = useReplay();
  const toast = useToast();
  const q = useQuery({ queryKey: ["households", dt?.id], queryFn: () => api.households(dt!.id), enabled: !!dt });
  const [seg, setSeg] = useState("all");
  const [flex, setFlex] = useState("all");
  const [search, setSearch] = useState("");
  const [density, setDensity] = useState<Density>("compact");
  const [open, setOpen] = useState<string | null>(null);
  const rows = useMemo(() => (q.data ?? []).filter((h) =>
    (seg === "all" || h.segment === seg) && (flex === "all" || h.flexibility === flex) &&
    (!search || h.id.toLowerCase().includes(search.toLowerCase()))), [q.data, seg, flex, search]);
  if (q.error) return <ErrorState title="Households did not load" body={(q.error as Error).message} onRetry={() => q.refetch()} />;
  if (!q.data || !dt) return <Skeleton className="h-96" />;
  const all = q.data;
  const copy = async () => {
    const csv = toCsv(rows);
    try { await navigator.clipboard.writeText(csv); toast({ title: "Copied as CSV", body: `${rows.length} rows on the clipboard.` }); }
    catch { toast({ title: "Copy blocked", body: "Your browser refused clipboard access. Select the table and copy it instead.", tone: "warn" }); }
  };
  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-lg">Households on {dt.id}</h1>
        <p className="text-sm text-muted">Anonymised. Year totals from the simulation; consent records are demo data.</p>
      </div>
      <Panel>
        <div className="grid grid-cols-2 gap-4 p-4 md:grid-cols-5">
          <Reading label="Homes" value={fmt.int(all.length)} />
          <Reading label="Inverter relay enrolled" value={fmt.int(all.filter((h) => h.flexibility === "inverter relay").length)} />
          <Reading label="Appliance actuator" value={fmt.int(all.filter((h) => h.flexibility === "appliance").length)} />
          <Reading label="Critical-load flag" value={fmt.int(all.filter((h) => h.critical).length)} />
          <Reading label="Opted out" value={fmt.int(all.filter((h) => h.enrolment === "opted out").length)} />
        </div>
      </Panel>
      <Panel title={`${rows.length} homes`} actions={
        <div className="flex flex-wrap items-end gap-2">
          <label className="relative" htmlFor="global-search">
            <span className="sr-only">Search households</span>
            <Search size={14} className="absolute left-2.5 top-2.5 text-muted" aria-hidden />
            <input id="global-search" placeholder="Search ID (/)" value={search} onChange={(e) => setSearch(e.target.value)}
              className="h-8 w-40 rounded-ctl border border-rule bg-raised pl-8 pr-2 text-sm" />
          </label>
          <Select id="seg-filter" value={seg} onValueChange={setSeg}
            options={[{ value: "all", label: "All segments" }, ...["Low-income", "Middle", "Affluent"].map((s) => ({ value: s, label: s }))]} />
          <Select id="flex-filter" value={flex} onValueChange={setFlex}
            options={[{ value: "all", label: "All flexibility" }, { value: "none", label: "None" }, { value: "inverter relay", label: "Inverter relay" }, { value: "appliance", label: "Appliance" }]} />
          <SegmentedControl label="Row density" value={density} onValueChange={(v) => setDensity(v as Density)}
            options={[{ value: "compact", label: "Compact" }, { value: "comfortable", label: "Comfortable" }]} />
          <Button size="sm" icon={<Copy size={14} />} onClick={copy}>Copy as CSV</Button>
        </div>}>
        {rows.length ? (
          <Table caption="Households" data={rows} density={density} onRowClick={(h) => setOpen(h.id)} maxHeight={600}
            columns={[
              { header: "ID", accessorKey: "id" },
              { header: "Segment", accessorKey: "segment" },
              { header: "Feeder", accessorKey: "lt_feeder", cell: (c) => `LT-${c.getValue()}` },
              { header: "Enrolment", accessorKey: "enrolment", cell: (c) => <StatusBadge status={c.getValue() === "opted out" ? "offline" : "ok"} label={String(c.getValue())} /> },
              { header: "Flexibility", accessorKey: "flexibility" },
              { header: "Band", accessorKey: "band_w", cell: (c) => fmt.watts(c.getValue() as number), meta: { align: "right" } },
              { header: "Critical", accessorKey: "critical", cell: (c) => (c.getValue() ? "Yes" : "–") },
              { header: "Curtailment (min, yr)", accessorKey: "curtailment_minutes_year", meta: { align: "right" }, cell: (c) => fmt.int(c.getValue() as number) },
              { header: "Outage h vs baseline", id: "out", accessorFn: (h) => h.outage_hours_year, meta: { align: "right" },
                cell: (c) => `${fmt.num1(c.row.original.outage_hours_year)} / ${fmt.num1(c.row.original.baseline_outage_hours_year)}` },
              { header: "Credits (yr)", accessorKey: "credits_year_rs", meta: { align: "right" }, cell: (c) => fmt.rupees(c.getValue() as number) },
            ]} />
        ) : <div className="p-4"><EmptyState title="No homes match these filters" body="Clear the search or choose All segments." /></div>}
      </Panel>
      <HouseholdDrawer id={open} onClose={() => setOpen(null)} />
    </div>
  );
}
