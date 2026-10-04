# Service blueprint

From enrolment to complaints, for one distribution transformer. The household and local
operator lanes are visible to the household; the SAANJH software and DISCOM lanes run
behind the line of visibility. The same blueprint is in the console under
Design → Service blueprint.

| Stage | Household | Local operator (RWA / SHG member / electrician) | SAANJH software (DT gateway + cloud) | DISCOM (sub-division, head-end, ADMS/DERMS) |
|---|---|---|---|---|
| 1. Enrolment | Hears about SAANJH from the local operator or a bill insert; agrees to the essential band; homes with an inverter may also agree to lend it | Reads consent aloud in the household's language, records it, flags critical loads with a reason | Stores consent, segment, critical flag and band; never stores appliance-level data | Enables load-limit control on the smart meters; signs the operating agreement |
| 2. Installation | Lets the operator fit a relay node on the inverter (inverter homes only); nothing is fitted in other homes | Fits the relay with the safety checklist; confirms the relay fails closed; uploads a photo | Registers the node; runs a relay test; adds the home to the flexibility list | Approves the node and battery installation; commissions the battery |
| 3. Day-ahead forecast | Gets a WhatsApp, SMS or voice-call notice: window, and what fits in 500 W | Calls critical-load homes and anyone who asked for a call | Forecasts demand and deficit (P10/P50/P90); plans the battery reserve; drafts the plan for approval | Sends the shortfall schedule or allocation (OpenADR / IEEE 2030.5 style) |
| 4. Shortfall event | Keeps lights, fans, fridge and phone on; switches off the geyser or iron if the band is on | On call during the window; checks the community battery's alarms | Runs the plan locally: rebound hold, relays, battery, band, last-resort disconnection; logs every decision with a reason | Sub-division engineer approves or modifies the plan in the console; the DT stays within its allocation |
| 5. Verification | Nothing to do | Confirms no home was left off by mistake; follows up flagged homes | Compares the event with the baseline (what rotational shedding would have done); computes outage minutes avoided and flexibility delivered | Accepts the measurement and verification report |
| 6. Credits and settlement | Sees credits on the bill (inverter homes) and a monthly summary message | Receives the monthly fee; explains credits to households | Computes credits per home (wear plus charging losses plus margin) and the DFPO report | Pays credits through billing; counts flexibility toward its DFPO |
| 7. Complaints | Replies COMPLAINT or calls the operator; can reply STOP at any time | Visits within 24 hours; escalates meter faults to the DISCOM | Opens a ticket, attaches the home's event history and meter data | Resolves meter and supply faults; reviews monthly complaint statistics |
