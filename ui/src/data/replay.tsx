import { useQuery } from "@tanstack/react-query";
import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { api, Day, DayInfo, DT } from "./api";

// Replay context: which DT, which simulated day, and the current 15-minute block.
// Playing advances one block every two seconds.

interface Replay {
  dts: DT[];
  dt: DT | null;
  setDtId: (id: string) => void;
  days: DayInfo[];
  date: string | null;
  setDate: (d: string) => void;
  block: number;
  setBlock: (b: number) => void;
  playing: boolean;
  setPlaying: (p: boolean) => void;
  day: Day | undefined;
  dayLoading: boolean;
  dayError: Error | null;
  staleMeter: boolean;
  setStaleMeter: (s: boolean) => void;
}

const Ctx = createContext<Replay | null>(null);
export const useReplay = () => {
  const c = useContext(Ctx);
  if (!c) throw new Error("useReplay outside ReplayProvider");
  return c;
};

function readPref(key: string) {
  try { return localStorage.getItem(key); } catch { return null; }
}
function writePref(key: string, v: string) {
  try { localStorage.setItem(key, v); } catch { /* ignore */ }
}

export function ReplayProvider({ children }: { children: React.ReactNode }) {
  const dtsQ = useQuery({ queryKey: ["dts"], queryFn: api.dts });
  const [dtId, setDtIdState] = useState<string | null>(readPref("saanjh.dt"));
  const dts = dtsQ.data ?? [];
  const dt = dts.find((d) => d.id === dtId) ?? dts[0] ?? null;
  const daysQ = useQuery({ queryKey: ["days", dt?.id], queryFn: () => api.days(dt!.id), enabled: !!dt });
  const days = daysQ.data ?? [];
  const [date, setDateState] = useState<string | null>(null);
  const activeDate = date && days.some((d) => d.date === date) ? date : (days.find((d) => d.featured) ?? days[0])?.date ?? null;
  const dayQ = useQuery({ queryKey: ["day", dt?.id, activeDate], queryFn: () => api.day(dt!.id, activeDate!), enabled: !!dt && !!activeDate });
  const [block, setBlock] = useState<number | null>(null);
  const [playing, setPlaying] = useState(false);
  const [staleMeter, setStaleMeter] = useState(false);

  // Start the replay an hour before the day's first shortfall, or at 17:00.
  const defaultBlock = useMemo(() => {
    const blocks = dayQ.data?.blocks ?? [];
    const b = blocks.find((x) => x.event_id && x.t >= 68) ?? blocks.find((x) => x.event_id);
    return b ? Math.max(0, b.t - 4) : 68;
  }, [dayQ.data]);
  const current = block ?? defaultBlock;

  useEffect(() => {
    if (!playing) return;
    const id = window.setInterval(() => setBlock((b) => {
      const next = (b ?? defaultBlock) + 1;
      if (next > 95) { setPlaying(false); return 95; }
      return next;
    }), 2000);
    return () => window.clearInterval(id);
  }, [playing, defaultBlock]);

  const value: Replay = {
    dts, dt,
    setDtId: (id) => { setDtIdState(id); writePref("saanjh.dt", id); setDateState(null); setBlock(null); },
    days, date: activeDate,
    setDate: (d) => { setDateState(d); setBlock(null); },
    block: current, setBlock, playing, setPlaying,
    day: dayQ.data, dayLoading: dtsQ.isLoading || daysQ.isLoading || dayQ.isLoading,
    dayError: (dtsQ.error || daysQ.error || dayQ.error) as Error | null,
    staleMeter, setStaleMeter,
  };
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
