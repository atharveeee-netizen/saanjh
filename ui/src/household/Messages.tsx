import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import { api, pickEvent } from "../data/api";
import { useReplay } from "../data/replay";
import { Panel, StatusBadge } from "../design/data";
import { fmtDate } from "../design/format";
import { cx } from "../design/primitives";
import { Lang, LANGS, REVIEW_NOTE } from "../i18n";
import { LangSwitch, PhoneFrame } from "../pages/PhoneFrame";

// Message flows for households. Times come from the replay day's first shortfall event.
type Msgs = Record<"dayahead" | "start" | "end" | "monthly" | "stop" | "help", { chat: string; sms: string }>;

function messages(lang: Lang, s: string, e: string, d: string, mins: number, credits: string): Msgs {
  if (lang === "hi") return {
    dayahead: { chat: `कल ${d} को ${s} से ${e} तक बिजली की कमी हो सकती है। आपके घर में बिजली रहेगी, पर सिर्फ़ 500 वाट तक: पंखा, बत्ती, फ्रिज और फोन चार्जिंग चलेंगे। गीज़र, प्रेस और मिक्सी उस समय न चलाएँ।`,
      sms: `SAANJH: कल ${s}-${e} बिजली 500W तक। पंखा,बत्ती,फ्रिज चलेंगे` },
    start: { chat: `अभी ${s} से ${e} तक सिर्फ़ ज़रूरी उपकरण चलाएँ। आपके घर की बिजली बंद नहीं होगी।`, sms: `SAANJH: ${s}-${e} सिर्फ़ ज़रूरी उपकरण। बिजली चालू रहेगी।` },
    end: { chat: `कमी ख़त्म हुई। अब सभी उपकरण चला सकते हैं।`, sms: `SAANJH: कमी ख़त्म। सभी उपकरण चला सकते हैं।` },
    monthly: { chat: `इस महीने कमी के दौरान आपके घर में ${mins} मिनट ज़रूरी बिजली रही। आपको ${credits} का क्रेडिट मिला।`, sms: `SAANJH: इस माह ${mins} मिनट ज़रूरी बिजली मिली। क्रेडिट ${credits}।` },
    stop: { chat: `आपने STOP भेजा। अगली कमी से आपका इन्वर्टर इस्तेमाल नहीं होगा। फिर जुड़ने के लिए START भेजें।`, sms: `SAANJH: STOP मिला। अगली बार से आप शामिल नहीं। फिर जुड़ें: START` },
    help: { chat: `मदद के लिए अपने स्थानीय ऑपरेटर को कॉल करें या COMPLAINT लिखकर भेजें।`, sms: `SAANJH मदद: स्थानीय ऑपरेटर को कॉल करें या COMPLAINT भेजें।` },
  };
  if (lang === "mr") return {
    dayahead: { chat: `उद्या ${d} रोजी ${s} ते ${e} वीज कमी पडू शकते. तुमच्या घरी वीज राहील, पण फक्त 500 वॅटपर्यंत: पंखा, दिवे, फ्रिज आणि फोन चार्जिंग चालेल. त्या वेळी गीझर, इस्त्री, मिक्सर वापरू नका.`,
      sms: `SAANJH: उद्या ${s}-${e} वीज 500W पर्यंत. पंखा,दिवे,फ्रिज चालेल` },
    start: { chat: `आता ${s} ते ${e} फक्त आवश्यक उपकरणे वापरा. तुमची वीज बंद होणार नाही.`, sms: `SAANJH: ${s}-${e} फक्त आवश्यक उपकरणे. वीज सुरू राहील.` },
    end: { chat: `तुटवडा संपला. आता सर्व उपकरणे वापरू शकता.`, sms: `SAANJH: तुटवडा संपला. सर्व उपकरणे वापरा.` },
    monthly: { chat: `या महिन्यात तुटवड्याच्या वेळी तुमच्या घरी ${mins} मिनिटे आवश्यक वीज होती. तुम्हाला ${credits} क्रेडिट मिळाले.`, sms: `SAANJH: या महिन्यात ${mins} मिनिटे आवश्यक वीज. क्रेडिट ${credits}.` },
    stop: { chat: `तुम्ही STOP पाठवले. पुढच्या तुटवड्यापासून तुमचा इन्व्हर्टर वापरला जाणार नाही. पुन्हा सामील होण्यासाठी START पाठवा.`, sms: `SAANJH: STOP मिळाले. पुढील वेळेपासून सहभाग नाही. पुन्हा: START` },
    help: { chat: `मदतीसाठी तुमच्या स्थानिक ऑपरेटरला फोन करा किंवा COMPLAINT लिहून पाठवा.`, sms: `SAANJH मदत: स्थानिक ऑपरेटरला फोन करा किंवा COMPLAINT पाठवा.` },
  };
  return {
    dayahead: { chat: `Tomorrow, ${d}, power may be short from ${s} to ${e}. Your home stays on, up to 500 W: fans, lights, fridge and phone charging will work. Please don't run the geyser, iron or mixer then.`,
      sms: `SAANJH: Tomorrow ${s}-${e} power limited to 500W. Fans, lights, fridge, phone OK. Avoid geyser/iron. Reply STOP to opt out` },
    start: { chat: `From now until ${e}, essentials only. Your power will stay on.`, sms: `SAANJH: ${s}-${e} essentials only (500W). Your power stays on.` },
    end: { chat: `The shortfall has ended. You can use all your appliances again.`, sms: `SAANJH: Shortfall over. You can use all appliances again.` },
    monthly: { chat: `This month your home kept essential power for ${mins} minutes during shortfalls. You earned ${credits} in credits.`, sms: `SAANJH: This month ${mins} min of essential power kept on. Credits earned: ${credits}.` },
    stop: { chat: `You sent STOP. From the next shortfall your inverter will not be used. Send START to join again.`, sms: `SAANJH: STOP received. You're out from the next event. Reply START to rejoin.` },
    help: { chat: `For help, call your local operator or reply COMPLAINT with your problem.`, sms: `SAANJH help: call your local operator or reply COMPLAINT.` },
  };
}

const GSM = /^[A-Za-z0-9 @£$¥èéùìòÇØøÅåΔ_ΦΓΛΩΠΨΣΘΞÆæßÉ!"#¤%&'()*+,\-./:;<=>?¡ÄÖÑÜ§¿äöñüà\n\r]*$/;
function smsInfo(text: string) {
  const unicode = !GSM.test(text);
  const len = [...text].length;
  const single = unicode ? 70 : 160, multi = unicode ? 67 : 153;
  const parts = len <= single ? 1 : Math.ceil(len / multi);
  return { unicode, len, single, parts };
}

function Bubble({ text, out, time }: { text: string; out?: boolean; time: string }) {
  return (
    <div className={cx("flex", out ? "justify-end" : "justify-start")}>
      <div className={cx("max-w-[85%] rounded-[10px] px-3 py-2 text-base", out ? "bg-accent-wash" : "border border-rule bg-raised")}>
        <p className="whitespace-pre-wrap">{text}</p>
        <p className="mt-1 text-right text-xs text-faint">{time}</p>
      </div>
    </div>
  );
}

export default function Messages() {
  const { dt, day } = useReplay();
  const [lang, setLang] = useState<Lang>("hi");
  const evQ = useQuery({ queryKey: ["events", dt?.id], queryFn: () => api.events(dt!.id), enabled: !!dt });
  const ev = pickEvent(evQ.data ?? [], day?.date);
  const s = ev?.start ?? "18:30", e = ev?.end ?? "20:30";
  const d = day ? fmtDate(day.date) : "";
  const m = messages(lang, s, e, d, 185, "Rs 64");
  const flows: [keyof Msgs, string, string][] = [
    ["dayahead", "Day-ahead notice", "Previous day, 19:00"], ["start", "Start of window", s], ["end", "End of window", e],
    ["monthly", "Monthly summary", "1st of the month"],
  ];
  const deva = lang !== "en" ? "font-deva" : "";
  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Link to="/operator" className="text-sm text-accent hover:underline">← Local operator app</Link>
          <h1 className="mt-1 text-xl">Household messages</h1>
          <p className="max-w-prose text-sm text-muted">Most low-income households will hear from SAANJH by WhatsApp, SMS or a voice call, not an app. Times below follow the replay day's first shortfall on {dt?.id}.</p>
        </div>
        <LangSwitch value={lang} onChange={setLang} options={LANGS} />
      </div>
      <p className="text-xs text-muted"><StatusBadge status="warn" label="Translation" /> {REVIEW_NOTE}</p>

      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
        <PhoneFrame label="Chat messages (rendered mock-up, no app branding)">
          <div className={cx("flex flex-col gap-3 bg-sunken px-3 py-4", deva)} lang={lang}>
            <p className="text-center text-xs text-muted">SAANJH · {dt?.id}</p>
            {flows.map(([k, , time]) => <Bubble key={k} text={m[k].chat} time={time} />)}
            <Bubble out text="STOP" time="21:02" />
            <Bubble text={m.stop.chat} time="21:02" />
            <Bubble out text="HELP" time="21:05" />
            <Bubble text={m.help.chat} time="21:05" />
          </div>
        </PhoneFrame>

        <Panel title="SMS versions" className="xl:col-span-2">
          <div className={cx("flex flex-col divide-y divide-[var(--rule)]", deva)} lang={lang}>
            {[...flows, ["stop", "Reply to STOP", ""] as [keyof Msgs, string, string], ["help", "Reply to HELP", ""] as [keyof Msgs, string, string]].map(([k, label]) => {
              const info = smsInfo(m[k].sms);
              const over = info.parts > 1;
              return (
                <div key={k} className="flex flex-col gap-1 px-4 py-3">
                  <div className="flex flex-wrap items-center justify-between gap-2 font-sans">
                    <span className="text-sm font-semibold">{label}</span>
                    <span className={cx("num text-xs", over ? "text-warn" : "text-muted")}>
                      {info.len} / {info.single} characters · {info.unicode ? "Unicode" : "GSM-7"} · {info.parts} SMS
                    </span>
                  </div>
                  <p className="text-base">{m[k].sms}</p>
                </div>
              );
            })}
          </div>
        </Panel>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Panel title="Reply keywords">
          <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 p-4 text-base">
            <dt className="font-semibold">STOP</dt><dd className="m-0">Opt out. Honoured from the next event at the latest; the household's inverter relay and appliance control are disabled. The essential band still applies, because it protects everyone on the DT.</dd>
            <dt className="font-semibold">START</dt><dd className="m-0">Join again.</dd>
            <dt className="font-semibold">HELP</dt><dd className="m-0">Local operator's number and how to complain.</dd>
            <dt className="font-semibold">COMPLAINT</dt><dd className="m-0">Opens a ticket for the local operator (follow-up within 24 hours) and the DISCOM call centre.</dd>
          </dl>
        </Panel>
        <Panel title="Voice call script for feature phones (IVR)">
          <ol className="flex list-decimal flex-col gap-2 py-4 pl-9 pr-4 text-base">
            <li>“Namaste. This is SAANJH for your electricity line {dt?.id}.”</li>
            <li>“Tomorrow between {s} and {e}, power will be limited, not cut. Fans, lights, fridge and phone charging will work.”</li>
            <li>“Press 1 to hear this again. Press 2 to talk to your local operator. Press 9 to stop receiving these calls.”</li>
            <li>No key pressed: the call repeats once, then ends with “Thank you.”</li>
            <li>Language is chosen at enrolment; the call is recorded in Hindi, Marathi and English.</li>
          </ol>
        </Panel>
      </div>
      <p className="text-sm"><Link to="/household/status" className="text-accent hover:underline">Open the household status page →</Link></p>
    </div>
  );
}
