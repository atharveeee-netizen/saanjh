import { useEffect, useMemo, useRef, useState } from "react";
import uPlot from "uplot";
import "uplot/dist/uPlot.min.css";
import { blockTime } from "./format";

export interface Series {
  key: string;
  label: string;
  values: (number | null)[];
  color: string;            // CSS variable name, e.g. "--series-net"
  width?: number;
  dash?: number[];
  step?: boolean;
  fill?: boolean;           // light area wash under the line
  directLabel?: boolean;
}

export interface ChartProps {
  series: Series[];
  band?: { lo: (number | null)[]; hi: (number | null)[]; label: string };
  rating?: { value: number; label: string };
  windows?: { from: number; to: number; label: string }[];
  now?: number;
  yLabel: string;
  unit?: string;
  height?: number;
  summary: string;           // text alternative for screen readers
  onBrush?: (from: number, to: number) => void;
}

const cssVar = (name: string) => getComputedStyle(document.documentElement).getPropertyValue(name).trim() || "#888";

/** Re-render charts when the theme changes (data-theme attribute or OS setting). */
export function useThemeVersion() {
  const [v, setV] = useState(0);
  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const bump = () => setV((x) => x + 1);
    mq.addEventListener("change", bump);
    const mo = new MutationObserver(bump);
    mo.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    return () => { mq.removeEventListener("change", bump); mo.disconnect(); };
  }, []);
  return v;
}

export function TimeSeriesChart({ series, band, rating, windows = [], now, yLabel, unit = "kW", height = 260, summary, onBrush }: ChartProps) {
  const host = useRef<HTMLDivElement>(null);
  const tip = useRef<HTMLDivElement>(null);
  const plot = useRef<uPlot | null>(null);
  const theme = useThemeVersion();
  const n = series[0]?.values.length ?? 0;
  const xs = useMemo(() => Array.from({ length: n }, (_, i) => i), [n]);

  useEffect(() => {
    const el = host.current;
    if (!el || !n) return;
    const ink = cssVar("--ink"), muted = cssVar("--ink-muted"), faint = cssVar("--ink-faint");
    const grid = cssVar("--chart-grid"), bandFill = cssVar("--accent-wash"), shade = cssVar("--surface-sunken");
    const font = `12px ${cssVar("--font-sans")}`;

    const data: uPlot.AlignedData = [xs, ...series.map((s) => s.values as number[])];
    const sOpts: uPlot.Series[] = [{ label: "Time" }];
    series.forEach((s) => sOpts.push({
      label: s.label, stroke: cssVar(s.color), width: s.width ?? 2, dash: s.dash,
      paths: s.step ? uPlot.paths.stepped!({ align: 1 }) : undefined,
      fill: s.fill ? cssVar(s.color) + "1f" : undefined, points: { show: false }, spanGaps: false,
    }));
    const bands: uPlot.Band[] = [];
    if (band) {
      data.push(band.hi as number[], band.lo as number[]);
      const hiIdx = data.length - 2, loIdx = data.length - 1;
      sOpts.push({ label: `${band.label} upper`, stroke: "transparent", points: { show: false } });
      sOpts.push({ label: `${band.label} lower`, stroke: "transparent", points: { show: false } });
      bands.push({ series: [hiIdx, loIdx], fill: bandFill });
    }

    const opts: uPlot.Options = {
      width: el.clientWidth, height,
      padding: [12, 96, 0, 0],
      legend: { show: false },
      cursor: { drag: { x: true, y: false, setScale: !onBrush }, points: { size: 8 } },
      scales: { x: { time: false } },
      bands,
      axes: [
        { stroke: muted, font, grid: { show: false }, ticks: { stroke: grid },
          values: (_u, vals) => vals.map((v) => (Number.isInteger(v) && v % 4 === 0 ? blockTime(v) : "")),
          incrs: [4, 8, 12, 24] },
        { stroke: muted, font, label: `${yLabel} (${unit})`, labelFont: font, labelSize: 18,
          grid: { stroke: grid, width: 1 }, ticks: { show: false }, size: 48 },
      ],
      series: sOpts,
      hooks: {
        drawClear: [(u) => {
          const ctx = u.ctx;
          ctx.save();
          for (const w of windows) {
            const x0 = u.valToPos(w.from, "x", true), x1 = u.valToPos(w.to, "x", true);
            ctx.fillStyle = shade;
            ctx.fillRect(x0, u.bbox.top, x1 - x0, u.bbox.height);
          }
          ctx.restore();
        }],
        draw: [(u) => {
          const ctx = u.ctx;
          const dpr = devicePixelRatio || 1;
          ctx.save();
          ctx.font = `${12 * dpr}px ${cssVar("--font-sans")}`;
          for (const w of windows) {
            const x0 = u.valToPos(w.from, "x", true);
            ctx.fillStyle = muted;
            ctx.fillText(w.label, x0 + 4 * dpr, u.bbox.top + 14 * dpr);
          }
          if (rating) {
            const y = u.valToPos(rating.value, "y", true);
            ctx.strokeStyle = faint; ctx.setLineDash([4 * dpr, 3 * dpr]); ctx.lineWidth = dpr;
            ctx.beginPath(); ctx.moveTo(u.bbox.left, y); ctx.lineTo(u.bbox.left + u.bbox.width, y); ctx.stroke();
            ctx.setLineDash([]); ctx.fillStyle = muted;
            ctx.fillText(rating.label, u.bbox.left + 4 * dpr, y - 4 * dpr);
          }
          if (now != null) {
            const x = u.valToPos(now, "x", true);
            ctx.strokeStyle = ink; ctx.lineWidth = 1.5 * dpr;
            ctx.beginPath(); ctx.moveTo(x, u.bbox.top); ctx.lineTo(x, u.bbox.top + u.bbox.height); ctx.stroke();
            ctx.fillStyle = ink; ctx.fillText("Now", x + 4 * dpr, u.bbox.top + u.bbox.height - 6 * dpr);
          }
          // Direct labels at line ends (text in ink, with a colour key beside it).
          const placed: number[] = [];
          series.forEach((s, i) => {
            if (s.directLabel === false) return;
            const vals = u.data[i + 1] as (number | null)[];
            let k = vals.length - 1;
            while (k >= 0 && vals[k] == null) k--;
            if (k < 0) return;
            let y = u.valToPos(vals[k] as number, "y", true);
            while (placed.some((p) => Math.abs(p - y) < 14 * dpr)) y += 14 * dpr;
            placed.push(y);
            const x = u.bbox.left + u.bbox.width + 6 * dpr;
            ctx.fillStyle = cssVar(s.color); ctx.fillRect(x, y - 1 * dpr, 8 * dpr, 2 * dpr);
            ctx.fillStyle = ink; ctx.fillText(s.label, x + 12 * dpr, y + 4 * dpr);
          });
          ctx.restore();
        }],
        setCursor: [(u) => {
          const t = tip.current;
          if (!t) return;
          const idx = u.cursor.idx;
          if (idx == null || u.cursor.left == null || u.cursor.left < 0) { t.hidden = true; return; }
          const rows = series.map((s, i) => {
            const v = u.data[i + 1][idx] as number | null;
            return `<div style="display:flex;gap:8px;align-items:center"><span style="width:8px;height:2px;background:${cssVar(s.color)}"></span><span style="flex:1">${s.label}</span><b>${v == null ? "–" : v.toFixed(1)}</b></div>`;
          });
          if (band) {
            const hi = band.hi[idx], lo = band.lo[idx];
            if (hi != null && lo != null) rows.push(`<div style="color:${muted}">${band.label}: ${lo.toFixed(1)}–${hi.toFixed(1)}</div>`);
          }
          t.innerHTML = `<div style="font-weight:600;margin-bottom:2px">${blockTime(idx)} IST · ${unit}</div>${rows.join("")}`;
          t.hidden = false;
          const left = Math.min(u.cursor.left + 64, el.clientWidth - 200);
          t.style.left = `${Math.max(0, left)}px`;
          t.style.top = `8px`;
        }],
        setSelect: [(u) => {
          if (!onBrush || u.select.width < 4) return;
          const a = Math.round(u.posToVal(u.select.left, "x")), b = Math.round(u.posToVal(u.select.left + u.select.width, "x"));
          onBrush(Math.max(0, a), Math.min(n - 1, b));
          u.setSelect({ left: 0, top: 0, width: 0, height: 0 }, false);
        }],
      },
    };
    plot.current?.destroy();
    plot.current = new uPlot(opts, data, el);
    const ro = new ResizeObserver(() => plot.current?.setSize({ width: el.clientWidth, height }));
    ro.observe(el);
    return () => { ro.disconnect(); plot.current?.destroy(); plot.current = null; };
  }, [series, band, rating, windows, now, height, theme, xs, n, yLabel, unit, onBrush]);

  return (
    <figure className="relative m-0 min-w-0">
      <div ref={host} className="w-full" role="img" aria-label={summary} />
      <div ref={tip} hidden className="pointer-events-none absolute z-10 w-48 rounded-ctl border border-rule bg-raised px-2 py-1.5 text-xs text-ink shadow-float" />
      <figcaption className="sr-only">{summary}</figcaption>
      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted" aria-hidden>
        {series.map((s) => (
          <span key={s.key} className="inline-flex items-center gap-1.5">
            <span className="inline-block h-0.5 w-4" style={{ background: `var(${s.color})`, borderTop: s.dash ? `2px dashed var(${s.color})` : undefined, height: s.dash ? 0 : 2 }} />
            {s.label}
          </span>
        ))}
        {band && <span className="inline-flex items-center gap-1.5"><span className="inline-block h-2.5 w-4 bg-accent-wash" />{band.label}</span>}
        {windows.length > 0 && <span className="inline-flex items-center gap-1.5"><span className="inline-block h-2.5 w-4 bg-sunken" />Supply shortfall window</span>}
      </div>
    </figure>
  );
}
