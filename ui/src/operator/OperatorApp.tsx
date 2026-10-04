import { useQuery } from "@tanstack/react-query";
import { BatteryCharging, CalendarClock, ClipboardList, Cloud, CloudOff, IndianRupee, PhoneCall, Wrench } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { api, pickEvent } from "../data/api";
import { useReplay } from "../data/replay";
import { StatusBadge } from "../design/data";
import { fmt, fmtDate } from "../design/format";
import { Button, cx, useToast } from "../design/primitives";
import { Lang, LANGS, REVIEW_NOTE, t } from "../i18n";
import { LangSwitch, PhoneFrame } from "../pages/PhoneFrame";

type Tab = "today" | "enrol" | "install" | "battery" | "payouts";
const TABS: { key: Tab; Icon: typeof CalendarClock }[] = [
  { key: "today", Icon: CalendarClock }, { key: "enrol", Icon: ClipboardList }, { key: "install", Icon: Wrench },
  { key: "battery", Icon: BatteryCharging }, { key: "payouts", Icon: IndianRupee },
];

function Field({ id, label, children }: { id: string; label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-base font-semibold">{label}</label>
      {children}
    </div>
  );
}
const input = "min-h-[48px] rounded-ctl border border-rule bg-raised px-3 text-md";

function Today({ lang }: { lang: Lang }) {
  const { dt, day } = useReplay();
  const evQ = useQuery({ queryKey: ["events", dt?.id], queryFn: () => api.events(dt!.id), enabled: !!dt });
  const hhQ = useQuery({ queryKey: ["households", dt?.id], queryFn: () => api.households(dt!.id), enabled: !!dt });
  const ev = pickEvent(evQ.data ?? [], day?.date);
  const critical = (hhQ.data ?? []).filter((h) => h.critical).slice(0, 4);
  const soc = day?.blocks[68]?.battery_soc_pct;
  return (
    <div className="flex flex-col gap-4">
      <section className="rounded-panel border border-rule p-4">
        <h2 className="text-sm text-muted">{t(lang, "next_window")}</h2>
        {ev ? <p className="num text-xl font-semibold">{ev.start}–{ev.end}</p> : <p className="text-md">–</p>}
        {day && <p className="text-sm text-muted">{fmtDate(day.date)} · {dt?.id}</p>}
      </section>
      <section className="rounded-panel border border-rule p-4">
        <h2 className="mb-2 text-base font-semibold">{t(lang, "homes_to_call")}</h2>
        <ul className="flex flex-col divide-y divide-[var(--rule)]">
          {critical.map((h) => (
            <li key={h.id} className="flex min-h-[48px] items-center justify-between gap-2">
              <span><b className="font-semibold">{h.id}</b><br /><span className="text-sm text-muted">{t(lang, "critical")} · {h.band_w} W</span></span>
              <Button size="md" variant="secondary" icon={<PhoneCall size={16} />} aria-label={`Call ${h.id}`}>{lang === "en" ? "Call" : lang === "hi" ? "कॉल" : "फोन"}</Button>
            </li>
          ))}
        </ul>
      </section>
      <section className="grid grid-cols-2 gap-3">
        <div className="rounded-panel border border-rule p-4">
          <h2 className="text-sm text-muted">{t(lang, "battery_status")}</h2>
          <p className="num text-xl font-semibold">{fmt.int(soc)}%</p>
          <p className="text-sm text-muted">{t(lang, "charged")}</p>
        </div>
        <div className="rounded-panel border border-rule p-4">
          <h2 className="text-sm text-muted">{t(lang, "open_complaints")}</h2>
          <p className="num text-xl font-semibold">2</p>
          <p className="text-xs text-muted">Example data</p>
        </div>
      </section>
    </div>
  );
}

function Enrol({ lang, onSaved }: { lang: Lang; onSaved: () => void }) {
  const toast = useToast();
  const [consent, setConsent] = useState(false);
  const [critical, setCritical] = useState(false);
  return (
    <form className="flex flex-col gap-4" onSubmit={(e) => {
      e.preventDefault();
      if (!consent) { toast({ title: t(lang, "consent"), body: "Read the consent aloud and tick the box before enrolling.", tone: "warn" }); return; }
      onSaved();
      toast({ title: t(lang, "enrolled"), body: t(lang, "enrolled_body") });
    }}>
      <fieldset className="flex flex-col gap-3 rounded-panel border border-rule p-4">
        <legend className="px-1 text-base font-semibold">{t(lang, "consent")}</legend>
        <label className="flex min-h-[48px] items-center gap-3 text-base">
          <input id="op-consent" type="checkbox" className="h-6 w-6" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
          {t(lang, "consent_read")}
        </label>
        <Field id="op-consent-audio" label={t(lang, "record_consent")}>
          <input id="op-consent-audio" type="file" accept="audio/*" className="text-sm" />
        </Field>
      </fieldset>
      <Field id="op-segment" label={t(lang, "segment")}>
        <select id="op-segment" className={input} defaultValue="">
          <option value="" disabled>{t(lang, "select")}</option>
          <option>{t(lang, "low_income")}</option><option>{t(lang, "middle")}</option><option>{t(lang, "affluent")}</option>
        </select>
      </Field>
      <label className="flex min-h-[48px] items-center gap-3 text-base">
        <input id="op-critical" type="checkbox" className="h-6 w-6" checked={critical} onChange={(e) => setCritical(e.target.checked)} />
        {t(lang, "critical")}
      </label>
      {critical && (
        <Field id="op-critical-reason" label={t(lang, "critical_reason")}>
          <input id="op-critical-reason" className={input} />
        </Field>
      )}
      <Field id="op-nameplate" label={t(lang, "nameplate")}>
        <input id="op-nameplate" type="file" accept="image/*" capture="environment" className="text-sm" />
      </Field>
      <Field id="op-meter" label={t(lang, "meter_no")}>
        <input id="op-meter" inputMode="numeric" className={input} placeholder="e.g. 4291 0063 77" />
      </Field>
      <Button type="submit" variant="primary" className="min-h-[48px]">{t(lang, "save_enrol")}</Button>
    </form>
  );
}

function Install({ lang, onSaved }: { lang: Lang; onSaved: () => void }) {
  const toast = useToast();
  const steps = ["step_isolate", "step_nc", "step_wire", "step_test", "step_photo"];
  const [done, setDone] = useState<boolean[]>(steps.map(() => false));
  const next = done.findIndex((d) => !d);
  return (
    <div className="flex flex-col gap-3">
      <h2 className="text-md font-semibold">{t(lang, "install_title")}</h2>
      <ol className="flex flex-col gap-2">
        {steps.map((s, i) => (
          <li key={s} className={cx("rounded-panel border p-3", i === next ? "border-accent" : "border-rule", i > next && next !== -1 && "opacity-60")}>
            <label className="flex min-h-[48px] items-start gap-3 text-base">
              <input type="checkbox" className="mt-1 h-6 w-6" checked={done[i]} disabled={i > next && next !== -1}
                onChange={(e) => setDone((d) => d.map((x, j) => (j === i ? e.target.checked : j > i ? false : x)))} />
              <span><span className="num mr-1 text-muted">{i + 1}.</span>{t(lang, s)}</span>
            </label>
            {s === "step_photo" && i === next && <input type="file" accept="image/*" capture="environment" className="ml-9 mt-1 text-sm" aria-label="Installation photo" />}
          </li>
        ))}
      </ol>
      <Button variant="primary" className="min-h-[48px]" disabled={next !== -1}
        onClick={() => { onSaved(); toast({ title: t(lang, "install_done"), body: t(lang, "enrolled_body") }); }}>
        {t(lang, "record_install")}
      </Button>
    </div>
  );
}

function Battery({ lang }: { lang: Lang }) {
  const { day } = useReplay();
  const b = day?.blocks[68];
  return (
    <div className="grid grid-cols-2 gap-3">
      {[
        [t(lang, "battery_status"), `${fmt.int(b?.battery_soc_pct)}% ${t(lang, "charged")}`],
        [t(lang, "temperature"), "34 °C"],
        [t(lang, "alarms"), t(lang, "none")],
        [t(lang, "last_inspection"), "12 Oct 2023"],
        [t(lang, "next_maintenance"), "12 Nov 2023"],
        ["Power", b ? (b.battery_kw >= 0 ? `${fmt.kw(b.battery_kw)} out` : `${fmt.kw(-b.battery_kw)} in`) : "–"],
      ].map(([k, v]) => (
        <div key={k} className="rounded-panel border border-rule p-3">
          <p className="text-sm text-muted">{k}</p><p className="num text-md font-semibold">{v}</p>
        </div>
      ))}
      <p className="col-span-2 text-xs text-muted">Temperature and inspection dates are example values; the charge level comes from the simulated replay day.</p>
    </div>
  );
}

function Payouts({ lang }: { lang: Lang }) {
  const { dt } = useReplay();
  const hhQ = useQuery({ queryKey: ["households", dt?.id], queryFn: () => api.households(dt!.id), enabled: !!dt });
  const metaQ = useQuery({ queryKey: ["meta"], queryFn: api.meta });
  const lenders = (hhQ.data ?? []).filter((h) => h.credits_year_rs > 0).sort((a, b) => b.credits_year_rs - a.credits_year_rs);
  const fee = metaQ.data?.economics?.scenarios?.[dt?.scenario ?? ""]?.reliability_only?.local_operator?.monthly_fee;
  return (
    <div className="flex flex-col gap-3">
      <div className="rounded-panel border border-rule p-4">
        <p className="text-sm text-muted">{t(lang, "operator_fee")}</p>
        <p className="num text-xl font-semibold">{fmt.rupees(fee)}</p>
      </div>
      <h2 className="text-base font-semibold">{t(lang, "credits_month")}</h2>
      <ul className="flex flex-col divide-y divide-[var(--rule)] rounded-panel border border-rule">
        {lenders.slice(0, 12).map((h) => (
          <li key={h.id} className="flex min-h-[48px] items-center justify-between px-3">
            <span>{h.id}</span><span className="num font-semibold">{fmt.rupees(h.credits_year_rs / 12)}</span>
          </li>
        ))}
      </ul>
      <p className="text-xs text-muted">Monthly credit = the household's simulated yearly credit divided by 12.</p>
    </div>
  );
}

export default function OperatorApp() {
  const [tab, setTab] = useState<Tab>("today");
  const [lang, setLang] = useState<Lang>("hi");
  const [pending, setPending] = useState(2);
  const [online, setOnline] = useState(false);
  const saved = () => setPending((p) => p + 1);
  return (
    <div className="flex min-h-full flex-col items-center gap-4 px-4 py-6">
      <div className="flex w-full max-w-[392px] flex-wrap items-center justify-between gap-2">
        <Link to="/" className="text-sm text-accent hover:underline">← Operator console</Link>
        <Link to="/household/messages" className="text-sm text-accent hover:underline">Household messages →</Link>
      </div>
      <PhoneFrame label="Local operator app (360 px). Works offline and syncs later.">
        <div className={cx("flex flex-col", lang !== "en" && "font-deva")} lang={lang}>
          <header className="flex flex-col gap-2 border-b border-rule px-4 py-3">
            <div className="flex items-center justify-between">
              <span className="font-semibold">SAANJH · DT-0423</span>
              <button onClick={() => { setOnline((o) => !o); if (!online) setPending(0); }}
                className="flex min-h-[36px] items-center gap-1 text-xs">
                {online ? <><Cloud size={14} className="text-ok" /> {t(lang, "synced")}</>
                  : <><CloudOff size={14} className="text-warn" /> {pending} {t(lang, "offline_sync")}</>}
              </button>
            </div>
            <LangSwitch value={lang} onChange={setLang} options={LANGS} />
          </header>
          <main className="px-4 py-4">
            {tab === "today" && <Today lang={lang} />}
            {tab === "enrol" && <Enrol lang={lang} onSaved={saved} />}
            {tab === "install" && <Install lang={lang} onSaved={saved} />}
            {tab === "battery" && <Battery lang={lang} />}
            {tab === "payouts" && <Payouts lang={lang} />}
          </main>
          <nav aria-label="Operator sections" className="sticky bottom-0 grid grid-cols-5 border-t border-rule bg-raised">
            {TABS.map(({ key, Icon }) => (
              <button key={key} onClick={() => setTab(key)} aria-current={tab === key ? "page" : undefined}
                className={cx("flex min-h-[56px] flex-col items-center justify-center gap-0.5 text-xs", tab === key ? "font-semibold text-accent" : "text-muted")}>
                <Icon size={20} aria-hidden />{t(lang, key)}
              </button>
            ))}
          </nav>
        </div>
      </PhoneFrame>
      <p className="max-w-[392px] text-xs text-muted"><StatusBadge status="warn" label="Translation" /> {REVIEW_NOTE}</p>
    </div>
  );
}
