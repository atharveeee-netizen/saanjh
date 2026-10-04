// Number, unit and time formatting. kW to 1 decimal, % whole numbers, rupees with
// Indian digit grouping, times as 24-hour IST, dates as "3 Oct 2026".

const inr = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });
const one = new Intl.NumberFormat("en-IN", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const zero = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });

export const fmt = {
  kw: (x: number | null | undefined) => (x == null ? "–" : `${one.format(x)} kW`),
  kwh: (x: number | null | undefined) => (x == null ? "–" : `${one.format(x)} kWh`),
  num1: (x: number | null | undefined) => (x == null ? "–" : one.format(x)),
  int: (x: number | null | undefined) => (x == null ? "–" : zero.format(x)),
  pct: (x: number | null | undefined) => (x == null ? "–" : `${zero.format(x)}%`),
  /** fraction 0..1 to whole percent */
  frac: (x: number | null | undefined) => (x == null ? "–" : `${zero.format(x * 100)}%`),
  volts: (x: number | null | undefined) => (x == null ? "–" : `${zero.format(x)} V`),
  amps: (x: number | null | undefined) => (x == null ? "–" : `${zero.format(x)} A`),
  watts: (x: number | null | undefined) => (x == null ? "–" : `${zero.format(x)} W`),
  hours: (x: number | null | undefined) => (x == null ? "–" : `${one.format(x)} h`),
  rupees: (x: number | null | undefined) => (x == null ? "–" : `Rs ${inr.format(Math.round(x))}`),
};

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** "2023-10-26" -> "26 Oct 2023" */
export function fmtDate(iso: string) {
  const [y, m, d] = iso.split("-").map(Number);
  return `${d} ${MONTHS[m - 1]} ${y}`;
}

/** block index 0..95 -> "18:15" */
export function blockTime(block: number) {
  const m = block * 15;
  return `${String(Math.floor(m / 60)).padStart(2, "0")}:${String(m % 60).padStart(2, "0")}`;
}

export const ist = (hhmm: string) => `${hhmm} IST`;

export function monthName(m: number) {
  return MONTHS[m - 1];
}
