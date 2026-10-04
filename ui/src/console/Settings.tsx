import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { mode, resetActions } from "../data/api";
import { useReplay } from "../data/replay";
import { Panel } from "../design/data";
import { Button, TextField, Toggle, useToast } from "../design/primitives";

export default function Settings() {
  const { staleMeter, setStaleMeter } = useReplay();
  const qc = useQueryClient();
  const toast = useToast();
  const [apiUrl, setApiUrl] = useState(() => { try { return localStorage.getItem("saanjh.api") || ""; } catch { return ""; } });
  const saveApi = () => {
    try {
      if (apiUrl) localStorage.setItem("saanjh.api", apiUrl); else localStorage.removeItem("saanjh.api");
      toast({ title: "Data source saved", body: "Reload the page to switch." });
    } catch { toast({ title: "Could not save", body: "This browser blocks local storage.", tone: "warn" }); }
  };
  return (
    <div className="flex max-w-3xl flex-col gap-4">
      <h1 className="text-lg">Settings</h1>
      <Panel title="Data source">
        <div className="flex flex-col gap-3 p-4">
          <p className="text-sm text-muted">Now reading: <b className="text-ink">{mode === "api" ? "SAANJH API" : "bundled replay data"}</b>. Every value is simulated on inputs calibrated to real data.</p>
          <TextField id="api-url" label="API address (leave empty for bundled data)" placeholder="http://localhost:8000"
            value={apiUrl} onChange={(e) => setApiUrl(e.target.value)} hint="Start the API with: uvicorn backend.main:app --port 8000" />
          <div><Button onClick={saveApi}>Save data source</Button></div>
        </div>
      </Panel>
      <Panel title="Training and demonstration">
        <div className="flex flex-col gap-4 p-4">
          <Toggle id="stale-toggle" label="Simulate delayed meter data" checked={staleMeter} onCheckedChange={setStaleMeter} />
          <div className="flex flex-wrap items-center gap-3">
            <Button variant="destructive" onClick={() => { resetActions(); qc.invalidateQueries(); toast({ title: "Operator actions cleared", body: "Approvals and cancellations made in this browser were removed." }); }}>
              Clear operator actions
            </Button>
            <span className="text-sm text-muted">Removes approvals, modifications and cancellations stored in this browser.</span>
          </div>
        </div>
      </Panel>
      <Panel title="Keyboard shortcuts">
        <dl className="grid grid-cols-[120px_1fr] gap-y-2 p-4 text-sm">
          <dt className="font-cond font-semibold">g o</dt><dd className="m-0">Overview</dd>
          <dt className="font-cond font-semibold">g e</dt><dd className="m-0">Events</dd>
          <dt className="font-cond font-semibold">g f / g h / g r</dt><dd className="m-0">Forecast, Households, Reports</dd>
          <dt className="font-cond font-semibold">/</dt><dd className="m-0">Search on Events and Households</dd>
          <dt className="font-cond font-semibold">a</dt><dd className="m-0">Approve the plan in the focused Next deficit window panel</dd>
        </dl>
      </Panel>
    </div>
  );
}
