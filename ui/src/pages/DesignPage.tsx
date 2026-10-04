import { Bell, Download, Filter } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { EmptyState, ErrorState, Panel, PhaseReading, Reading, Skeleton, Sparkline, StatusBadge, Stepper } from "../design/data";
import {
  Breadcrumb, Button, Checkbox, Dialog, Drawer, IconButton, Kbd, Popover, SegmentedControl, Select, Tabs, TextField,
  Toggle, Tooltip, useToast,
} from "../design/primitives";
import { Density, Table } from "../design/Table";
import { TimeSeriesChart } from "../design/TimeSeriesChart";

const TOKENS = [
  ["--surface", "Drawing sheet"], ["--surface-raised", "Panels"], ["--surface-sunken", "Wells, table headers"],
  ["--ink", "Primary text"], ["--ink-muted", "Secondary text"], ["--rule", "1px dividers"],
  ["--accent", "Interactive only"], ["--accent-wash", "Selection, forecast band"],
  ["--phase-r", "Phase R"], ["--phase-y", "Phase Y"], ["--phase-b", "Phase B"],
  ["--status-ok", "Normal"], ["--status-warn", "Watch"], ["--status-alarm", "Alarm"],
  ["--series-net", "Chart: DT load"], ["--series-baseline", "Chart: baseline"], ["--series-battery", "Chart: battery"], ["--series-pv", "Chart: PV"],
];

const demo = Array.from({ length: 96 }, (_, t) => {
  const h = t / 4;
  const base = 22 + 6 * Math.sin(((h - 7) / 24) * 2 * Math.PI) + (h > 17.5 && h < 23 ? 24 * Math.sin(((h - 17.5) / 5.5) * Math.PI) : 0);
  return Math.round(base * 10) / 10;
});

export default function DesignPage() {
  const toast = useToast();
  const [seg, setSeg] = useState("day");
  const [sel, setSel] = useState("500");
  const [chk, setChk] = useState(true);
  const [tog, setTog] = useState(false);
  const [tab, setTab] = useState("a");
  const [dlg, setDlg] = useState(false);
  const [drw, setDrw] = useState(false);
  const [density, setDensity] = useState<Density>("comfortable");
  const rows = [
    { id: "HH-0423-031", segment: "Low-income", band: 500, minutes: 120 },
    { id: "HH-0423-032", segment: "Middle", band: 500, minutes: 45 },
    { id: "HH-0423-033", segment: "Affluent", band: 1000, minutes: 0 },
  ];
  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-xl">SAANJH design system</h1>
          <p className="text-sm text-muted">Tokens and components for the operator console, the local operator app and the household pages.</p>
        </div>
        <div className="flex gap-3 text-sm">
          <Link className="text-accent hover:underline" to="/">Operator console</Link>
          <Link className="text-accent hover:underline" to="/design/service-blueprint">Service blueprint</Link>
        </div>
      </header>

      <Panel title="Colour">
        <div className="grid grid-cols-2 gap-3 p-4 sm:grid-cols-3 lg:grid-cols-6">
          {TOKENS.map(([v, use]) => (
            <div key={v} className="flex flex-col gap-1">
              <span className="h-10 rounded-panel border border-rule" style={{ background: `var(${v})` }} />
              <code className="font-cond text-xs">{v}</code>
              <span className="text-xs text-muted">{use}</span>
            </div>
          ))}
        </div>
        <p className="px-4 pb-4 text-sm text-muted">Status is always colour, icon and word. Phase colours appear only on per-phase data. The accent marks things you can act on.</p>
      </Panel>

      <Panel title="Type">
        <div className="flex flex-col gap-2 p-4">
          <p className="text-2xl font-semibold">32 · DT-0423 at 94% loading</p>
          <p className="text-xl font-semibold">24 · Next deficit window 18:15–20:30 IST</p>
          <p className="text-lg font-semibold">20 · Plan approved</p>
          <p className="text-md">16 · Essential supply kept for 248 of 250 homes</p>
          <p className="text-base">14 · Body text. Rupees use Indian grouping: Rs 3,17,767. Dates read 3 Oct 2026.</p>
          <p className="text-sm text-muted">13 · Secondary text and labels</p>
          <p className="font-cond text-xs font-semibold text-muted">12 · IBM Plex Sans Condensed for dense table headers and diagram labels</p>
          <p className="font-deva text-md">आपके घर में बिजली रहेगी · तुमच्या घरात वीज राहील</p>
        </div>
      </Panel>

      <div className="grid gap-6 lg:grid-cols-2">
        <Panel title="Actions">
          <div className="flex flex-wrap items-center gap-3 p-4">
            <Button variant="primary" onClick={() => toast({ title: "Plan approved", body: "EV-0423-1026-1815 will run as planned." })}>Approve plan</Button>
            <Button variant="secondary">Modify</Button>
            <Button variant="quiet">Open event</Button>
            <Button variant="destructive">Cancel event</Button>
            <Button variant="primary" loading>Approving</Button>
            <IconButton label="Filter rows"><Filter size={16} /></IconButton>
            <IconButton label="Notifications"><Bell size={16} /></IconButton>
            <Tooltip content="Downloads are disabled in the hosted demo"><span><Button icon={<Download size={14} />} disabled>Export</Button></span></Tooltip>
          </div>
        </Panel>
        <Panel title="Inputs">
          <div className="grid gap-4 p-4 sm:grid-cols-2">
            <TextField id="d-reserve" label="Battery reserve (kWh)" defaultValue="42" hint="0 to 80 kWh" />
            <TextField id="d-err" label="Band floor (W)" defaultValue="250" error="Use 300 W or more." />
            <Select id="d-sel" label="Band" value={sel} onValueChange={setSel} options={[{ value: "1000", label: "1,000 W" }, { value: "500", label: "500 W" }, { value: "300", label: "300 W" }]} />
            <div className="flex flex-col gap-3">
              <SegmentedControl label="Theme" value={seg} onValueChange={setSeg} options={[{ value: "day", label: "Day" }, { value: "night", label: "Night shift" }]} />
              <Checkbox id="d-chk" label="Critical load" checked={chk} onCheckedChange={setChk} />
              <Toggle id="d-tog" label="Simulate delayed data" checked={tog} onCheckedChange={setTog} />
            </div>
          </div>
        </Panel>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Panel title="Overlays and navigation">
          <div className="flex flex-col gap-4 p-4">
            <Breadcrumb items={[{ label: "Demo Circle" }, { label: "Division 2" }, { label: "Sub-division 4" }, { label: "DT-0423, 100 kVA" }]} />
            <div className="flex flex-wrap gap-3">
              <Button onClick={() => setDlg(true)}>Open dialog</Button>
              <Button onClick={() => setDrw(true)}>Open drawer</Button>
              <Popover trigger={<Button>Open popover</Button>}><p className="text-sm">Popover content with a short explanation.</p></Popover>
              <span className="flex items-center gap-2 text-sm text-muted">Go to overview <Kbd keys={["g", "o"]} /></span>
            </div>
            <Tabs label="Example tabs" value={tab} onValueChange={setTab} items={[
              { value: "a", label: "Monthly reliability", content: <p className="text-sm">Tab content.</p> },
              { value: "b", label: "Demand flexibility", content: <p className="text-sm">Second tab.</p> },
            ]} />
            <Stepper steps={["Forecast", "Plan", "Approved", "Dispatching", "Completed", "Verified"]} current={2} />
          </div>
        </Panel>
        <Panel title="Readings and states">
          <div className="grid gap-4 p-4 sm:grid-cols-2">
            <Reading label="DT loading" value="94" unit="%" status="warn" at="18:15 IST" />
            <PhaseReading label="Phase current" values={[118, 96, 104]} unit="A" />
            <div className="flex flex-col gap-1">
              <StatusBadge status="ok" /><StatusBadge status="warn" /><StatusBadge status="alarm" /><StatusBadge status="offline" /><StatusBadge status="stale" />
            </div>
            <Sparkline values={demo} label="Demand sparkline" width={180} height={36} limit={40} />
          </div>
        </Panel>
      </div>

      <Panel title="Table">
        <div className="flex justify-end px-4 pt-3">
          <SegmentedControl label="Density" value={density} onValueChange={(v) => setDensity(v as Density)} options={[{ value: "compact", label: "Compact" }, { value: "comfortable", label: "Comfortable" }]} />
        </div>
        <Table caption="Example households" data={rows} density={density} selectable
          columns={[{ header: "ID", accessorKey: "id" }, { header: "Segment", accessorKey: "segment" },
            { header: "Band (W)", accessorKey: "band", meta: { align: "right" } }, { header: "Curtailed (min)", accessorKey: "minutes", meta: { align: "right" } }]} />
      </Panel>

      <Panel title="Time series">
        <div className="p-4">
          <TimeSeriesChart yLabel="Power" summary="Example time series with a forecast band, the DT rating and a shaded shortfall window."
            series={[{ key: "n", label: "DT load", values: demo, color: "--series-net" }, { key: "p", label: "Rooftop PV", values: demo.map((_, t) => Math.max(0, 12 * Math.sin(((t / 4 - 6) / 12.5) * Math.PI))), color: "--series-pv", width: 1.5 }]}
            band={{ lo: demo.map((v) => v * 0.9), hi: demo.map((v) => v * 1.1), label: "Forecast P10–P90" }}
            rating={{ value: 45, label: "DT rating" }} windows={[{ from: 74, to: 82, label: "Shortfall" }]} now={70} />
        </div>
      </Panel>

      <div className="grid gap-6 lg:grid-cols-3">
        <EmptyState title="No events match" body="Clear the search or choose All months." />
        <ErrorState title="Meter data delayed" body="Meter data for DT-0423 hasn't arrived since 17:40 IST. Showing the last known state." onRetry={() => {}} />
        <div className="flex flex-col gap-2"><Skeleton className="h-6 w-1/2" /><Skeleton className="h-24" /><Skeleton className="h-6" /></div>
      </div>

      <Dialog open={dlg} onOpenChange={setDlg} title="Modify plan" description="Dialogs carry a title, a short description and actions."
        footer={<><Button onClick={() => setDlg(false)}>Keep current plan</Button><Button variant="primary" onClick={() => setDlg(false)}>Save modified plan</Button></>}>
        <p className="text-sm">Dialog body.</p>
      </Dialog>
      <Drawer open={drw} onOpenChange={setDrw} title="LT feeder 2" subtitle="Readings at 18:15 IST"><p className="text-sm">Drawer body.</p></Drawer>
    </div>
  );
}
