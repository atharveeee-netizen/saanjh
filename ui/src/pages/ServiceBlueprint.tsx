import { Link } from "react-router-dom";

// Service blueprint: who does what at each stage, from enrolment to complaints.
// The same content is in docs/SERVICE_BLUEPRINT.md.

export const STAGES = ["Enrolment", "Installation", "Day-ahead forecast", "Shortfall event", "Verification", "Credits and settlement", "Complaints"];
export const LANES: { lane: string; kind: "front" | "back"; cells: string[] }[] = [
  { lane: "Household", kind: "front", cells: [
    "Hears about SAANJH from the local operator or a bill insert; agrees to the essential band; homes with an inverter may also agree to lend it",
    "Lets the operator fit a relay node on the inverter (inverter homes only); nothing is fitted in other homes",
    "Gets a WhatsApp, SMS or voice-call notice: window, and what fits in 500 W",
    "Keeps lights, fans, fridge and phone on; switches off the geyser or iron if the band is on",
    "Nothing to do",
    "Sees credits on the bill (inverter homes) and a monthly summary message",
    "Replies COMPLAINT or calls the operator; can reply STOP at any time",
  ] },
  { lane: "Local operator (RWA / SHG member / electrician)", kind: "front", cells: [
    "Reads consent aloud in the household's language, records it, flags critical loads with a reason",
    "Fits the relay with the safety checklist; confirms the relay fails closed; uploads a photo",
    "Calls critical-load homes and anyone who asked for a call",
    "On call during the window; checks the community battery's alarms",
    "Confirms no home was left off by mistake; follows up flagged homes",
    "Receives the monthly fee; explains credits to households",
    "Visits within 24 hours; escalates meter faults to the DISCOM",
  ] },
  { lane: "SAANJH software (gateway at the DT + cloud)", kind: "back", cells: [
    "Stores consent, segment, critical flag and band; never stores appliance-level data",
    "Registers the node; runs a relay test; adds the home to the flexibility list",
    "Forecasts demand and deficit (P10/P50/P90); plans the battery reserve; drafts the plan for approval",
    "Runs the plan locally: rebound hold, relays, battery, band, last-resort disconnection; logs every decision with a reason",
    "Compares the event with the baseline (what rotational shedding would have done); computes outage minutes avoided and flexibility delivered",
    "Computes credits per home (wear plus charging losses plus margin) and the DFPO report",
    "Opens a ticket, attaches the home's event history and meter data",
  ] },
  { lane: "DISCOM (sub-division, head-end, ADMS/DERMS)", kind: "back", cells: [
    "Enables load-limit control on the smart meters; signs the operating agreement",
    "Approves the node and battery installation; commissions the battery",
    "Sends the shortfall schedule or allocation (OpenADR / IEEE 2030.5 style)",
    "Sub-division engineer approves or modifies the plan in the console; the DT stays within its allocation",
    "Accepts the measurement and verification report",
    "Pays credits through billing; counts flexibility toward its DFPO",
    "Resolves meter and supply faults; reviews monthly complaint statistics",
  ] },
];

export default function ServiceBlueprint() {
  return (
    <div className="mx-auto flex max-w-[1400px] flex-col gap-4 px-4 py-6">
      <div>
        <Link to="/design" className="text-sm text-accent hover:underline">← Design system</Link>
        <h1 className="mt-1 text-xl">Service blueprint</h1>
        <p className="max-w-prose text-sm text-muted">From enrolment to complaints, for one distribution transformer. The top two lanes are what people see and do; the bottom two run behind the line of visibility.</p>
      </div>
      <div className="overflow-x-auto rounded-panel border border-rule bg-raised">
        <table className="w-full min-w-[1100px] border-collapse text-left text-sm">
          <caption className="sr-only">SAANJH service blueprint</caption>
          <thead>
            <tr>
              <th scope="col" className="w-48 border-b border-r border-rule bg-sunken px-3 py-2 font-cond text-xs text-muted">Lane</th>
              {STAGES.map((s, i) => (
                <th key={s} scope="col" className="border-b border-rule bg-sunken px-3 py-2 font-cond text-xs font-semibold text-ink">
                  <span className="num text-muted">{i + 1}.</span> {s}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {LANES.map((l, li) => (
              <tr key={l.lane} className={li === 2 ? "border-t-2 border-dashed border-t-[var(--ink-faint)]" : ""}>
                <th scope="row" className="border-b border-r border-rule px-3 py-3 align-top text-sm font-semibold">
                  {l.lane}
                  <span className="mt-1 block text-xs font-normal text-muted">{l.kind === "front" ? "Visible to the household" : "Behind the line of visibility"}</span>
                </th>
                {l.cells.map((c, i) => (
                  <td key={i} className="border-b border-rule px-3 py-3 align-top leading-5">{c}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-muted">The dashed line between lanes 2 and 3 is the line of visibility. Stages are in time order, so they are numbered.</p>
    </div>
  );
}
