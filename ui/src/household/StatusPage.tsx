import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import { api, pickEvent } from "../data/api";
import { useReplay } from "../data/replay";
import { cx } from "../design/primitives";
import { Lang, LANGS, t } from "../i18n";
import { LangSwitch, PhoneFrame } from "../pages/PhoneFrame";

// The page a household opens from a message: plain status, what fits in the band, and
// (for homes that lend an inverter battery) their reserve and credits. Kept light so it
// loads on a cheap phone over a slow connection.

const APPLIANCES: { key: string; en: string; hi: string; mr: string; w: number }[] = [
  { key: "fan", en: "Ceiling fan", hi: "पंखा", mr: "पंखा", w: 60 },
  { key: "light", en: "4 LED lights", hi: "4 एलईडी बत्ती", mr: "4 एलईडी दिवे", w: 40 },
  { key: "fridge", en: "Fridge", hi: "फ्रिज", mr: "फ्रिज", w: 120 },
  { key: "tv", en: "TV", hi: "टीवी", mr: "टीव्ही", w: 70 },
  { key: "phone", en: "Phone charging", hi: "फोन चार्जिंग", mr: "फोन चार्जिंग", w: 10 },
  { key: "cooler", en: "Air cooler", hi: "कूलर", mr: "कूलर", w: 180 },
  { key: "iron", en: "Iron", hi: "प्रेस", mr: "इस्त्री", w: 1000 },
  { key: "geyser", en: "Geyser", hi: "गीज़र", mr: "गीझर", w: 2000 },
];

export default function StatusPage() {
  const { dt, day } = useReplay();
  const [lang, setLang] = useState<Lang>("hi");
  const [on, setOn] = useState<Record<string, boolean>>({ fan: true, light: true, fridge: true, phone: true });
  const evQ = useQuery({ queryKey: ["events", dt?.id], queryFn: () => api.events(dt!.id), enabled: !!dt });
  const ev = pickEvent(evQ.data ?? [], day?.date);
  const band = 500;
  const used = APPLIANCES.filter((a) => on[a.key]).reduce((s, a) => s + a.w, 0);
  const over = used > band;
  const deva = lang !== "en" ? "font-deva" : "";
  return (
    <div className="flex min-h-full flex-col items-center gap-4 px-4 py-6">
      <Link to="/household/messages" className="self-center text-sm text-accent hover:underline">← Household messages</Link>
      <PhoneFrame label="Household status page (360 px, under 150 KB of its own content)">
        <div className={cx("flex flex-col gap-4 px-4 py-5", deva)} lang={lang}>
          <LangSwitch value={lang} onChange={setLang} options={LANGS} />
          <section className="rounded-panel border-2 border-ok p-4">
            <p className="text-xl font-semibold text-ink">{t(lang, "home_on")}</p>
            <p className="mt-1 text-md text-ink">
              {lang === "en" ? `${t(lang, "essentials_until")} ${ev?.end ?? "20:30"}.` : `${ev?.end ?? "20:30"} ${t(lang, "essentials_until")}।`}
            </p>
          </section>
          <section>
            <h2 className="mb-2 text-md font-semibold">{t(lang, "what_fits")} ({band} W)</h2>
            <div className="flex flex-wrap gap-2">
              {APPLIANCES.map((a) => (
                <button key={a.key} onClick={() => setOn((o) => ({ ...o, [a.key]: !o[a.key] }))} aria-pressed={!!on[a.key]}
                  className={cx("min-h-[44px] rounded-full border px-3 text-base", on[a.key] ? "border-accent bg-accent-wash font-semibold" : "border-rule")}>
                  {a[lang]} · {a.w} W
                </button>
              ))}
            </div>
            <div className="mt-3 h-3 w-full rounded-full bg-sunken" role="meter" aria-valuemin={0} aria-valuemax={band} aria-valuenow={used} aria-label="Power in use">
              <div className={cx("h-3 rounded-full", over ? "bg-alarm" : "bg-ok")} style={{ width: `${Math.min(100, (used / band) * 100)}%` }} />
            </div>
            <p className={cx("num mt-1 text-md font-semibold", over ? "text-alarm" : "text-ok")}>
              {used} W / {band} W {over ? (lang === "en" ? "– too much, switch something off" : lang === "hi" ? "– ज़्यादा है, कुछ बंद करें" : "– जास्त आहे, काहीतरी बंद करा") : "✓"}
            </p>
          </section>
          <section className="rounded-panel border border-rule p-4">
            <p className="text-base">{t(lang, "battery_kept")}</p>
            <p className="mt-2 text-sm text-muted">{t(lang, "credits")}: Rs 64 (example)</p>
          </section>
        </div>
      </PhoneFrame>
    </div>
  );
}
