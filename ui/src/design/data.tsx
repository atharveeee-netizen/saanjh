import { AlertTriangle, CheckCircle2, CircleSlash, Clock3, OctagonAlert, RefreshCw, Check } from "lucide-react";
import React from "react";
import { cx } from "./primitives";

/* ---------------------------------------------------------------- StatusBadge
   Status is always colour + icon + word. */
export type Status = "ok" | "warn" | "alarm" | "offline" | "stale";
const STATUS: Record<Status, { cls: string; Icon: typeof CheckCircle2; word: string }> = {
  ok: { cls: "text-ok", Icon: CheckCircle2, word: "Normal" },
  warn: { cls: "text-warn", Icon: AlertTriangle, word: "Watch" },
  alarm: { cls: "text-alarm", Icon: OctagonAlert, word: "Alarm" },
  offline: { cls: "text-offline", Icon: CircleSlash, word: "Offline" },
  stale: { cls: "text-warn", Icon: Clock3, word: "Stale data" },
};
export function StatusBadge({ status, label }: { status: Status; label?: string }) {
  const s = STATUS[status];
  return (
    <span className={cx("inline-flex items-center gap-1 whitespace-nowrap text-sm font-semibold", s.cls)}>
      <s.Icon size={14} aria-hidden strokeWidth={2.25} />
      {label ?? s.word}
    </span>
  );
}

/* ---------------------------------------------------------------- Reading */
export function Reading({ label, value, unit, delta, at, status, size = "md" }:
  { label: string; value: React.ReactNode; unit?: string; delta?: React.ReactNode; at?: string;
    status?: Status; size?: "md" | "lg" }) {
  return (
    <div className="flex min-w-0 flex-col gap-0.5">
      <span className="text-xs text-muted">{label}</span>
      <span className="flex items-baseline gap-1">
        <span className={cx("num font-semibold text-ink", size === "lg" ? "text-xl" : "text-md")}>{value}</span>
        {unit && <span className="text-sm text-muted">{unit}</span>}
      </span>
      {(delta || at || status) && (
        <span className="flex flex-wrap items-center gap-2 text-xs text-muted">
          {status && <StatusBadge status={status} />}
          {delta && <span>{delta}</span>}
          {at && <span>{at}</span>}
        </span>
      )}
    </div>
  );
}

/* ---------------------------------------------------------------- PhaseReading (R/Y/B) */
export function PhaseReading({ label, values, unit }: { label: string; values: [number, number, number]; unit: string }) {
  const phases: [string, string][] = [["R", "bg-phase-r"], ["Y", "bg-phase-y"], ["B", "bg-phase-b"]];
  const max = Math.max(1, ...values);
  return (
    <div className="flex min-w-0 flex-col gap-1">
      <span className="text-xs text-muted">{label}</span>
      <div className="flex flex-col gap-0.5">
        {phases.map(([p, bg], i) => (
          <div key={p} className="flex items-center gap-2 text-sm">
            <span className={cx("inline-block h-2.5 w-2.5 rounded-full", bg)} aria-hidden />
            <span className="w-3 font-cond font-semibold text-muted">{p}</span>
            <span className="num w-12 text-right font-semibold">{Math.round(values[i])}</span>
            <span className="text-xs text-muted">{unit}</span>
            <span className="h-1 flex-1 rounded-full bg-sunken" aria-hidden>
              <span className={cx("block h-1 rounded-full", bg)} style={{ width: `${(values[i] / max) * 100}%` }} />
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------- Sparkline */
export function Sparkline({ values, width = 96, height = 24, limit, label }:
  { values: number[]; width?: number; height?: number; limit?: number; label: string }) {
  if (!values.length) return null;
  const max = Math.max(...values, limit ?? -Infinity);
  const min = Math.min(0, ...values);
  const x = (i: number) => (i / (values.length - 1 || 1)) * (width - 4) + 2;
  const y = (v: number) => height - 2 - ((v - min) / (max - min || 1)) * (height - 4);
  const d = values.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join("");
  const last = values[values.length - 1];
  return (
    <svg width={width} height={height} role="img" aria-label={label} className="overflow-visible">
      <path d={`${d}L${x(values.length - 1)},${height - 2}L${x(0)},${height - 2}Z`} fill="var(--accent-wash)" />
      {limit != null && <line x1={0} x2={width} y1={y(limit)} y2={y(limit)} stroke="var(--ink-faint)" strokeDasharray="2 2" strokeWidth={1} />}
      <path d={d} fill="none" stroke="var(--accent)" strokeWidth={1.5} strokeLinejoin="round" />
      <circle cx={x(values.length - 1)} cy={y(last)} r={2.5} fill="var(--accent)" />
    </svg>
  );
}

/* ---------------------------------------------------------------- Stepper
   Only for genuinely sequential workflows. */
export function Stepper({ steps, current }: { steps: string[]; current: number }) {
  return (
    <ol className="flex flex-wrap items-center gap-x-1 gap-y-2" aria-label="Progress">
      {steps.map((s, i) => {
        const done = i < current, active = i === current;
        return (
          <li key={s} className="flex items-center gap-1" aria-current={active ? "step" : undefined}>
            <span className={cx("flex h-5 w-5 items-center justify-center rounded-full border text-xs font-semibold",
              done ? "border-ok bg-ok text-white" : active ? "border-accent text-accent" : "border-rule text-faint")}>
              {done ? <Check size={12} strokeWidth={3} aria-hidden /> : i + 1}
            </span>
            <span className={cx("text-sm", active ? "font-semibold text-ink" : done ? "text-ink" : "text-muted")}>{s}</span>
            {i < steps.length - 1 && <span className={cx("mx-1 h-px w-6", done ? "bg-ok" : "bg-rule")} aria-hidden />}
          </li>
        );
      })}
    </ol>
  );
}

/* ---------------------------------------------------------------- States */
export function EmptyState({ title, body, action }: { title: string; body: string; action?: React.ReactNode }) {
  return (
    <div className="flex flex-col items-start gap-2 rounded-panel border border-dashed border-rule px-5 py-6">
      <p className="text-base font-semibold">{title}</p>
      <p className="max-w-prose text-sm text-muted">{body}</p>
      {action}
    </div>
  );
}

export function ErrorState({ title, body, onRetry }: { title: string; body: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="flex flex-col items-start gap-2 rounded-panel border border-l-4 border-l-alarm bg-raised px-5 py-4">
      <StatusBadge status="alarm" label={title} />
      <p className="max-w-prose text-sm text-ink">{body}</p>
      {onRetry && (
        <button onClick={onRetry} className="inline-flex items-center gap-1 text-sm font-semibold text-accent hover:underline">
          <RefreshCw size={14} aria-hidden /> Try again
        </button>
      )}
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div aria-hidden className={cx("animate-pulse rounded-panel bg-sunken", className)} />;
}

/* ---------------------------------------------------------------- Panel */
export function Panel({ title, actions, children, className, id }:
  { title?: React.ReactNode; actions?: React.ReactNode; children: React.ReactNode; className?: string; id?: string }) {
  return (
    <section id={id} className={cx("min-w-0 rounded-panel border border-rule bg-raised", className)}>
      {(title || actions) && (
        <header className="flex flex-wrap items-center justify-between gap-2 border-b border-rule px-4 py-2.5">
          {typeof title === "string" ? <h2 className="text-base font-semibold">{title}</h2> : title}
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </header>
      )}
      <div className="min-w-0">{children}</div>
    </section>
  );
}
