import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, DEvent } from "../data/api";
import { useReplay } from "../data/replay";
import { Button, Dialog, SegmentedControl, TextField, useToast } from "../design/primitives";

const USABLE_KWH = 80; // 100 kWh pack, 10-90% window

export function ModifyPlanDialog({ open, onOpenChange, event }: { open: boolean; onOpenChange: (o: boolean) => void; event: DEvent }) {
  const { dt } = useReplay();
  const qc = useQueryClient();
  const toast = useToast();
  const [reserve, setReserve] = useState(String(Math.min(USABLE_KWH, Math.round(event.mv.deficit_kwh || 40))));
  const [band, setBand] = useState("500");
  const [note, setNote] = useState("");
  const r = Number(reserve);
  const invalid = !Number.isFinite(r) || r < 0 || r > USABLE_KWH;
  const m = useMutation({
    mutationFn: () => api.act(dt!.id, event.id, "modify", { battery_reserve_kwh: r, band_floor_w: Number(band), note }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["events"] });
      qc.invalidateQueries({ queryKey: ["event", event.id] });
      toast({ title: "Plan modified", body: `Battery reserve ${r} kWh, band floor ${band} W.` });
      onOpenChange(false);
    },
    onError: (e: Error) => toast({ title: "Could not modify the plan", body: e.message, tone: "alarm" }),
  });
  return (
    <Dialog open={open} onOpenChange={onOpenChange} title={`Modify plan for ${event.id}`}
      description={`${event.start}–${event.end} IST. Changes apply to this event only.`}
      footer={<>
        <Button variant="secondary" onClick={() => onOpenChange(false)}>Keep current plan</Button>
        <Button variant="primary" disabled={invalid} loading={m.isPending} onClick={() => m.mutate()}>Save modified plan</Button>
      </>}>
      <div className="flex flex-col gap-5">
        <TextField id="reserve-kwh" label="Community battery energy kept for this window (kWh)" type="number" min={0} max={USABLE_KWH}
          value={reserve} onChange={(e) => setReserve(e.target.value)}
          hint={`Between 0 and ${USABLE_KWH} kWh usable (10–90% of the 100 kWh pack).`}
          error={invalid ? `Enter a value from 0 to ${USABLE_KWH} kWh.` : undefined} />
        <div className="flex flex-col gap-2">
          <span className="text-sm font-semibold">Lowest essential band allowed</span>
          <SegmentedControl label="Lowest essential band" value={band} onValueChange={setBand}
            options={[{ value: "1000", label: "1,000 W" }, { value: "750", label: "750 W" }, { value: "500", label: "500 W" }, { value: "300", label: "300 W" }]} />
          <p className="text-xs text-muted">The gateway always starts at the gentlest band. A lower floor avoids disconnections in deep shortfalls; homes flagged critical keep 1,000 W.</p>
        </div>
        <TextField id="modify-note" label="Note for the log (optional)" value={note} onChange={(e) => setNote(e.target.value)} />
      </div>
    </Dialog>
  );
}
