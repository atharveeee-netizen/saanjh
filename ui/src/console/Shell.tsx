import {
  BarChart3, CalendarClock, FileText, Gauge, Home, ListOrdered, Menu, Moon, PanelLeftClose, PanelLeftOpen,
  Settings as SettingsIcon, Sun, Users,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useReplay } from "../data/replay";
import { StatusBadge } from "../design/data";
import { blockTime, fmtDate } from "../design/format";
import { Breadcrumb, cx, IconButton, Kbd, Tooltip } from "../design/primitives";

const NAV = [
  { to: "/", label: "Overview", Icon: Home, key: "o" },
  { to: "/events", label: "Events", Icon: ListOrdered, key: "e" },
  { to: "/forecast", label: "Forecast", Icon: CalendarClock, key: "f" },
  { to: "/households", label: "Households", Icon: Users, key: "h" },
  { to: "/reports", label: "Reports", Icon: FileText, key: "r" },
  { to: "/fleet", label: "Transformers", Icon: BarChart3, key: "t" },
  { to: "/settings", label: "Settings", Icon: SettingsIcon, key: "s" },
];

function readTheme(): "light" | "dark" {
  const attr = document.documentElement.getAttribute("data-theme");
  if (attr === "dark" || attr === "light") return attr;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export default function Shell() {
  const { dt, date, block, staleMeter } = useReplay();
  const nav = useNavigate();
  const loc = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileNav, setMobileNav] = useState(false);
  const [theme, setTheme] = useState(readTheme);
  const pending = useRef<string | null>(null);

  // Keyboard shortcuts: g then o/e/f/h/r/t/s navigates; "/" focuses search.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || e.metaKey || e.ctrlKey || e.altKey) return;
      if (pending.current === "g") {
        const hit = NAV.find((n) => n.key === e.key);
        pending.current = null;
        if (hit) { e.preventDefault(); nav(hit.to); }
        return;
      }
      if (e.key === "g") { pending.current = "g"; window.setTimeout(() => (pending.current = null), 1200); }
      if (e.key === "/") {
        const s = document.getElementById("global-search") as HTMLInputElement | null;
        if (s) { e.preventDefault(); s.focus(); }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [nav]);

  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    try { localStorage.setItem("saanjh.theme", next); } catch { /* ignore */ }
    setTheme(next);
  };

  const navList = (
    <ul className="flex flex-col gap-0.5 p-2">
      {NAV.map(({ to, label, Icon, key }) => (
        <li key={to}>
          <NavLink to={to} end={to === "/"} onClick={() => setMobileNav(false)}
            className={({ isActive }) => cx("flex h-9 items-center gap-3 rounded-ctl px-2.5 text-base",
              isActive ? "bg-accent-wash font-semibold text-ink" : "text-muted hover:bg-sunken hover:text-ink")}>
            <Icon size={18} aria-hidden className="shrink-0" />
            {!collapsed && <span className="flex-1">{label}</span>}
            {!collapsed && <span className="hidden xl:inline"><Kbd keys={["g", key]} /></span>}
          </NavLink>
        </li>
      ))}
    </ul>
  );

  return (
    <div className="flex min-h-full flex-col">
      <header className="sticky top-0 z-30 flex flex-wrap items-center gap-x-4 gap-y-2 border-b border-rule bg-raised px-4 py-2"
        style={{ top: "env(safe-area-inset-top, 0px)" }}>
        <div className="flex items-center gap-2">
          <IconButton label="Open navigation" className="lg:hidden" onClick={() => setMobileNav((x) => !x)}><Menu size={18} /></IconButton>
          <span className="flex items-center gap-2 font-semibold">
            <Gauge size={18} aria-hidden className="text-accent" />
            SAANJH
          </span>
        </div>
        <div className="min-w-0 flex-1">
          {dt && <Breadcrumb items={[{ label: dt.circle }, { label: dt.division }, { label: dt.subdivision },
            { label: dt.name, onClick: loc.pathname !== "/" ? () => nav("/") : undefined }]} />}
        </div>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
          {date && (
            <Tooltip content="Replay of a simulated day. Use the replay controls on the Overview to move through it.">
              <span className="num text-ink">{fmtDate(date)}, <b>{blockTime(block)} IST</b></span>
            </Tooltip>
          )}
          {staleMeter ? <StatusBadge status="stale" label="Meter data 18 min old" />
            : <span className="text-muted">Meter data 3 min old</span>}
          <IconButton label={theme === "dark" ? "Switch to day theme" : "Switch to night-shift theme"} onClick={toggleTheme}>
            {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
          </IconButton>
          <span className="hidden items-center gap-2 sm:flex">
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-sunken text-xs font-semibold" aria-hidden>SD</span>
            <span className="text-muted">SDO duty engineer</span>
          </span>
        </div>
      </header>

      <div className="flex flex-1">
        <nav aria-label="Main" className={cx("no-print hidden shrink-0 border-r border-rule bg-raised lg:flex lg:flex-col", collapsed ? "w-14" : "w-56")}>
          {navList}
          <div className="mt-auto p-2">
            <IconButton label={collapsed ? "Expand navigation" : "Collapse navigation"} onClick={() => setCollapsed((c) => !c)}>
              {collapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
            </IconButton>
          </div>
        </nav>
        {mobileNav && (
          <nav aria-label="Main" className="fixed inset-x-0 top-[52px] z-30 border-b border-rule bg-raised shadow-float lg:hidden">{navList}</nav>
        )}
        <main className="min-w-0 flex-1 px-4 py-4 lg:px-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
