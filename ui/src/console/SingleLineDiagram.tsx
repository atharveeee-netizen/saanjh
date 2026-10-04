import type { Block, DT, Household } from "../data/api";
import { fmt } from "../design/format";

// Single-line diagram of the distribution transformer: 11 kV incomer -> DT -> LV busbar
// -> community battery and four LT feeders -> homes. Drawn in SVG with --ink strokes;
// state is shown by colour plus shape plus words.

export type SldElement =
  | { kind: "incomer" } | { kind: "dt" } | { kind: "battery" } | { kind: "gateway" }
  | { kind: "feeder"; index: number };

const W = 960, H = 470;
const BUS_Y = 214;
const FEEDER_X = [330, 480, 630, 780];

function loadingStatus(pct: number) {
  return pct > 100 ? "alarm" : pct > 90 ? "warn" : "ok";
}
const statusVar = { ok: "var(--status-ok)", warn: "var(--status-warn)", alarm: "var(--status-alarm)" };
const statusWord = { ok: "Normal", warn: "High loading", alarm: "Overloaded" };

function Hit({ label, onSelect, children }: { label: string; onSelect: () => void; children: React.ReactNode }) {
  return (
    <g role="button" tabIndex={0} aria-label={label} className="cursor-pointer outline-none [&:focus-visible>rect.focus]:stroke-[var(--accent)]"
      onClick={onSelect} onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onSelect(); } }}>
      {children}
    </g>
  );
}

export function SingleLineDiagram({ dt, block, homes, onSelect }:
  { dt: DT; block: Block; homes: Household[]; onSelect: (e: SldElement) => void }) {
  const st = loadingStatus(block.loading_pct);
  const shortfall = block.allocation_kw != null;
  const batt = block.battery_kw;
  const soc = block.battery_soc_pct ?? 0;
  const perFeeder = [0, 1, 2, 3].map((f) => homes.filter((h) => h.lt_feeder === f + 1));
  const fb = (block as any).feeder_banded as number[] | undefined;
  const fs = (block as any).feeder_shed as number[] | undefined;
  const fkw = (block as any).feeder_kw as number[] | undefined;
  const ink = "var(--ink)", muted = "var(--ink-muted)", rule = "var(--rule)";
  const text = { fontFamily: "var(--font-cond)", fontSize: 12, fill: muted } as const;
  const strong = { fontFamily: "var(--font-sans)", fontSize: 13, fontWeight: 600, fill: ink } as const;

  return (
    <div className="overflow-x-auto">
      <svg viewBox={`0 0 ${W} ${H}`} className="block h-auto w-full min-w-[640px]" role="group"
        aria-label={`Single-line diagram of ${dt.name}. Loading ${Math.round(block.loading_pct)} percent, ${statusWord[st]}. ${block.homes_banded} homes on essential band, ${block.homes_shed} disconnected.`}>
        {/* ---------------- 11 kV incomer */}
        <Hit label={`11 kV incomer ${dt.feeder_11kv}`} onSelect={() => onSelect({ kind: "incomer" })}>
          <rect className="focus" x={120} y={6} width={250} height={70} fill="transparent" stroke="transparent" strokeWidth={2} rx={2} />
          <line x1={150} y1={14} x2={150} y2={62} stroke={ink} strokeWidth={2} />
          <rect x={141} y={30} width={18} height={18} fill="var(--surface-raised)" stroke={ink} strokeWidth={2} />
          <text x={168} y={26} style={strong}>{dt.feeder_11kv}</text>
          <text x={168} y={42} style={text}>11 kV incomer, breaker closed</text>
          <text x={168} y={58} style={{ ...text, fill: shortfall ? "var(--status-warn)" : muted, fontWeight: shortfall ? 600 : 400 }}>
            {shortfall ? `Supply limited to ${fmt.kw(block.allocation_kw)} (cut ${Math.round(block.cut_pct)}%)` : "Supply unrestricted"}
          </text>
        </Hit>
        <line x1={150} y1={62} x2={150} y2={92} stroke={ink} strokeWidth={2} />

        {/* ---------------- Distribution transformer */}
        <Hit label={`Distribution transformer ${dt.name}, loading ${Math.round(block.loading_pct)} percent`} onSelect={() => onSelect({ kind: "dt" })}>
          <rect className="focus" x={96} y={88} width={290} height={96} fill="transparent" stroke="transparent" strokeWidth={2} rx={2} />
          <circle cx={150} cy={114} r={20} fill="none" stroke={ink} strokeWidth={2} />
          <circle cx={150} cy={142} r={20} fill="none" stroke={ink} strokeWidth={2} />
          <text x={186} y={112} style={strong}>{dt.id}, {dt.rating_kva} kVA, 11/0.433 kV</text>
          <text x={186} y={146} style={{ fontFamily: "var(--font-sans)", fontSize: 28, fontWeight: 600, fill: ink }}>{Math.round(block.loading_pct)}%</text>
          <text x={250} y={146} style={text}>loading, {fmt.kw(block.net_kw)}</text>
          <circle cx={192} cy={166} r={5} fill={statusVar[st]} />
          <text x={202} y={170} style={{ ...text, fill: statusVar[st], fontWeight: 600 }}>{statusWord[st]}</text>
        </Hit>
        <line x1={150} y1={162} x2={150} y2={BUS_Y} stroke={ink} strokeWidth={2} />
        {/* DT meter */}
        <circle cx={150} cy={190} r={9} fill="var(--surface-raised)" stroke={ink} strokeWidth={1.5} />
        <text x={146} y={194} style={{ ...text, fontSize: 10, fill: ink }}>M</text>

        {/* ---------------- Gateway (data link dashed) */}
        <Hit label="SAANJH gateway at the transformer" onSelect={() => onSelect({ kind: "gateway" })}>
          <rect className="focus" x={420} y={96} width={170} height={60} fill="transparent" stroke="transparent" strokeWidth={2} />
          <line x1={162} y1={190} x2={430} y2={126} stroke={muted} strokeWidth={1} strokeDasharray="4 3" />
          <rect x={430} y={106} width={150} height={40} fill="var(--surface-raised)" stroke={ink} strokeWidth={1.5} rx={2} />
          <text x={442} y={124} style={strong}>SAANJH gateway</text>
          <text x={442} y={139} style={text}>Plan running locally</text>
        </Hit>

        {/* ---------------- LV busbar */}
        <line x1={60} y1={BUS_Y} x2={880} y2={BUS_Y} stroke={ink} strokeWidth={5} />
        <text x={884} y={BUS_Y + 4} style={text}>415 V</text>

        {/* ---------------- Community battery */}
        <Hit label={`Community battery, ${Math.round(soc)} percent, ${batt > 0 ? "discharging" : batt < 0 ? "charging" : "idle"} ${Math.abs(batt).toFixed(1)} kilowatts`} onSelect={() => onSelect({ kind: "battery" })}>
          <rect className="focus" x={20} y={BUS_Y + 6} width={250} height={170} fill="transparent" stroke="transparent" strokeWidth={2} />
          <line x1={90} y1={BUS_Y} x2={90} y2={BUS_Y + 40} stroke={ink} strokeWidth={2} />
          <rect x={70} y={BUS_Y + 40} width={40} height={30} fill="var(--surface-raised)" stroke={ink} strokeWidth={1.5} />
          <text x={78} y={BUS_Y + 60} style={{ ...text, fill: ink }}>PCS</text>
          <line x1={90} y1={BUS_Y + 70} x2={90} y2={BUS_Y + 96} stroke={ink} strokeWidth={2} />
          {/* battery symbol: long and short plates */}
          {[0, 1, 2].map((i) => (
            <g key={i}>
              <line x1={70} y1={BUS_Y + 96 + i * 12} x2={110} y2={BUS_Y + 96 + i * 12} stroke={ink} strokeWidth={2} />
              <line x1={80} y1={BUS_Y + 102 + i * 12} x2={100} y2={BUS_Y + 102 + i * 12} stroke={ink} strokeWidth={4} />
            </g>
          ))}
          {/* flow arrow */}
          {Math.abs(batt) > 0.05 && (
            <path d={batt > 0 ? `M122 ${BUS_Y + 60} l0 -26 l-6 8 m6 -8 l6 8` : `M122 ${BUS_Y + 30} l0 26 l-6 -8 m6 8 l6 -8`}
              stroke="var(--series-battery)" strokeWidth={2.5} fill="none" />
          )}
          <text x={136} y={BUS_Y + 44} style={strong}>Community battery</text>
          <text x={136} y={BUS_Y + 60} style={text}>Second-life LFP, 100 kWh</text>
          <rect x={136} y={BUS_Y + 70} width={110} height={10} fill="none" stroke={rule} />
          <rect x={136} y={BUS_Y + 70} width={110 * Math.max(0, Math.min(1, soc / 100))} height={10} fill="var(--series-battery)" />
          <text x={136} y={BUS_Y + 96} style={{ ...text, fill: ink }}>{Math.round(soc)}% charged</text>
          <text x={136} y={BUS_Y + 112} style={text}>
            {batt > 0.05 ? `Discharging ${fmt.kw(batt)}` : batt < -0.05 ? `Charging ${fmt.kw(-batt)}` : "Idle"}
          </text>
        </Hit>

        {/* ---------------- LT feeders and homes */}
        {FEEDER_X.map((x, f) => {
          const hs = perFeeder[f];
          const n = hs.length;
          const banded = fb ? fb[f] : 0;
          const shed = fs ? fs[f] : 0;
          const cols = 13;
          return (
            <Hit key={f} label={`LT feeder ${f + 1}: ${n} homes, ${banded} on essential band, ${shed} disconnected`} onSelect={() => onSelect({ kind: "feeder", index: f })}>
              <rect className="focus" x={x - 62} y={BUS_Y + 6} width={130} height={246} fill="transparent" stroke="transparent" strokeWidth={2} />
              <line x1={x} y1={BUS_Y} x2={x} y2={BUS_Y + 70} stroke={ink} strokeWidth={2} />
              <rect x={x - 7} y={BUS_Y + 24} width={14} height={14} fill="var(--surface-raised)" stroke={ink} strokeWidth={1.5} />
              <text x={x + 12} y={BUS_Y + 35} style={text}>LT-{f + 1}</text>
              {fkw && <text x={x + 12} y={BUS_Y + 51} style={{ ...text, fill: ink }}>{fmt.kw(fkw[f])}</text>}
              {/* pole */}
              <line x1={x - 20} y1={BUS_Y + 70} x2={x + 20} y2={BUS_Y + 70} stroke={ink} strokeWidth={2} />
              <text x={x - 58} y={BUS_Y + 88} style={text}>{n} homes</text>
              {hs.map((h, i) => {
                const r = Math.floor(i / cols), c = i % cols;
                const hx = x - 58 + c * 9, hy = BUS_Y + 96 + r * 9;
                const state = i < shed ? "shed" : i < shed + banded ? "band" : "on";
                return state === "on"
                  ? <rect key={h.id} x={hx} y={hy} width={7} height={7} fill="none" stroke={muted} strokeWidth={1} />
                  : state === "band"
                    ? <g key={h.id}><rect x={hx} y={hy} width={7} height={7} fill="none" stroke="var(--status-warn)" strokeWidth={1} />
                        <rect x={hx} y={hy + 3.5} width={7} height={3.5} fill="var(--status-warn)" /></g>
                    : <g key={h.id}><rect x={hx} y={hy} width={7} height={7} fill="var(--status-alarm)" />
                        <path d={`M${hx + 1} ${hy + 1}l5 5m0 -5l-5 5`} stroke="var(--surface-raised)" strokeWidth={1.2} /></g>;
              })}
              <text x={x - 58} y={BUS_Y + 100 + Math.ceil(n / cols) * 9 + 12} style={{ ...text, fill: banded || shed ? ink : muted }}>
                {shed ? `${shed} off, ` : ""}{banded} on band
              </text>
            </Hit>
          );
        })}

        {/* ---------------- Legend */}
        <g transform={`translate(20 ${H - 26})`} style={text}>
          <rect x={0} y={0} width={9} height={9} fill="none" stroke={muted} />
          <text x={14} y={9} style={text}>Full supply</text>
          <rect x={90} y={0} width={9} height={9} fill="none" stroke="var(--status-warn)" />
          <rect x={90} y={4.5} width={9} height={4.5} fill="var(--status-warn)" />
          <text x={104} y={9} style={text}>Essentials only (band)</text>
          <rect x={248} y={0} width={9} height={9} fill="var(--status-alarm)" />
          <text x={262} y={9} style={text}>Disconnected</text>
          <line x1={360} y1={5} x2={384} y2={5} stroke={muted} strokeDasharray="4 3" />
          <text x={390} y={9} style={text}>Data link</text>
          <text x={470} y={9} style={text}>Select any element for its readings.</text>
        </g>
      </svg>
    </div>
  );
}
