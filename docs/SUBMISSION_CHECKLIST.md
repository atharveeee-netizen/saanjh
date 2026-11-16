# Submission checklist — Prototype Phase

**Deadline: 7 December 2026, 23:59 IST. Portal: YouNoodle.**
Round 1 is cleared; this checklist covers the Prototype Phase package for the
Schneider Electric Yuva Yodha 2026 submission, track *Grid Reliability &
Renewable Intermittency*.

Work backwards from **7 December 18:00 IST**, not 23:59. Portal uploads fail at
the worst possible moment.

## 1. What must be true

| # | Requirement | Evidence | State |
|---|---|---|---|
| 1 | Reliability scorecard | `simulation/results/reliability.json`, dashboard tab 1 | ✅ |
| 2 | Battery vs deferred energy reconciliation | `simulation/results/energy_balance.json`, dashboard tab 2 | ✅ |
| 3 | Low-income, three adoption groups | `simulation/results/low_income.json`, dashboard tab 3 | ✅ |
| 4 | Overload and sensitivity | `simulation/results/overload.json`, dashboard tab 4 | ✅ |
| 5 | Packet-loss and dropout robustness | `simulation/results/robustness.json`, dashboard tab 4 | ✅ |
| 6 | Indian calibration | `simulation/results/calibration.json`, dashboard tab 5 | ✅ |
| 7 | LoRa driver and protocol | `gateway/lora_driver.py`, `gateway/protocol.py`, `firmware/rak4631_node/` | ✅ |
| 8 | Dashboard: KPI, live node, DISCOM view | `dashboard/app.py`, seven tabs | ✅ |
| 9 | Ownership, O&M, BOM, limitations | `docs/OWNERSHIP_MODEL.md`, `docs/BOM.md`, `docs/LIMITATIONS.md` | ✅ |
| 10 | Tests and fresh-clone runnability | 90 Python tests, 34 native C++ tests, CI quickstart job | ✅ |
| 11 | 2–3 RAK4631 nodes with battery, dummy load, relay | `firmware/rak4631_node/`, `docs/HARDWARE.md` | ⚠️ builds, not bench-validated |
| 12 | ~10 s telemetry, command listen, relay transfer, 70% refusal, opt-out | firmware + 34 native tests | ⚠️ logic tested, not bench-validated |
| 13 | CM4 + SX1262 Python gateway: CSV/SQLite, Streamlit, 154 kW replay | `gateway/`, `gateway/data/`, dashboard tab 6 | ✅ replay; ⚠️ live pending |
| 14 | Demo video | `docs/DEMO.md` script | ⬜ record |

Legend: ✅ done, ⚠️ partial, ⬜ not started.

## 2. Artefacts to upload or link

| Artefact | Path | Notes |
|---|---|---|
| Written submission | `docs/WRITEUP.md` | The long-form document |
| Project brief | `docs/PROJECT_BRIEF.md` | Facts and ground rules |
| Repository | `https://github.com/atharveeee-netizen/saanjh` | MIT licence |
| Demo video | _to record_ | 3–5 min, follows `docs/DEMO.md` |
| Dashboard screenshots | `docs/figures/` | Refresh if the UI changes |
| Architecture diagrams | `docs/architecture/*.svg` | Mermaid + SVG |
| BOM | `docs/BOM.md` | Rough prices, labelled |
| Limitations | `docs/LIMITATIONS.md` | Do not hide this |
| Replay evidence | `gateway/data/replay_summary.json` | Labelled seeded replay |
| Test evidence | CI run + `pytest -q` + `pio test -e native` | Screenshot or log |

If the portal limits file size, link the repository and attach the write-up and
video. Do not attach the SQLite database or raw CSVs unless asked.

## 3. The three evidence claims to get right

Reviewers will probe these. Have the answers ready.

### 3.1 The headline is simulated, not field data

> "98% essential availability is a simulation over 30 Monte Carlo seeds on
> inputs calibrated to NASA POWER, Prayas eMARC and Prayas ESMI. It is not a
> field trial. The hardware proves the control path, not the system benefit."

### 3.2 The energy claim was corrected downward

> "The legacy 45-minute case claimed 42.19 kWh. The audit delivers 7.22 kWh and
> shows 34.97 kWh unmet. The identity holds. The annual result does not depend
> on the legacy number."

### 3.3 The hardware is a ≤12 V bench prototype

> "Three RAK4631 nodes, a 12 V dummy load, a relay, a LiFePO4 pack and a CM4
> gateway. No mains. The relay's NC contact is the grid path, so reset and fault
> both return the load to grid. The node enforces the 70% reserve itself."

## 4. Final verification (run on 6 December)

```bash
# 1. Fresh clone, not the working tree
git clone https://github.com/atharveeee-netizen/saanjh.git /tmp/saanjh-check
cd /tmp/saanjh-check
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

# 2. One-command check
python scripts/run_all.py --quick

# 3. Firmware
cd firmware/rak4631_node
pio run -e node101 -e node102 -e node103
pio test -e native

# 4. Dashboard renders
cd ../..
streamlit run dashboard/app.py
```

Acceptance gates:

* `run_all.py --quick` ends `All requested stages completed.`
* `pytest -q` reports **90 passed**.
* `pio test -e native` reports **34 tests, 0 failures**.
* All three firmware images link, each under 6% RAM and 15% flash.
* Dashboard renders seven tabs with no exception.
* `python scripts/render_results.py --check` exits 0.
* `python -m simulation.contracts` validates 7 bundles and the gateway summary.

## 5. Repository hygiene before submission

* [ ] `git status` is clean; no `.pio/`, `.venv/`, `__pycache__/` or logs staged.
* [ ] `LICENSE` is MIT and matches `docs/OPEN_SOURCE_NOTICES.md`.
* [ ] `README.md` quick start works from a fresh clone.
* [ ] No secrets, tokens, personal paths or private links in the tree.
* [ ] The stale FUXA page is either regenerated or clearly marked non-critical.
* [ ] The demo video does not show a private dashboard link or API key.
* [ ] `docs/LIMITATIONS.md` is linked from the README.
* [ ] The latest commit is pushed and CI is green.

## 6. Demo video plan (record 5 December)

| Time | Shot | Audio |
|---|---|---|
| 0:00–0:30 | Problem: dark feeder, headline numbers | The 59% → 98% claim, labelled simulated |
| 0:30–1:15 | Architecture diagram | Three layers: meter band, gateway, node |
| 1:15–2:00 | Dashboard tab 1 and 2 | Reliability and the energy correction |
| 2:00–2:40 | Dashboard tab 3 | Three low-income routes and payback |
| 2:40–3:20 | Dashboard tab 4 and 5 | Robustness and Indian calibration |
| 3:20–4:20 | Bench: nodes, relay click, serial ACK | 70% refusal and opt-out |
| 4:20–5:00 | Limitations and next step | Bench, not field; 20–50 homes next |

Recording rules:

* Show the replay/live badge explicitly. Never let a replay look live.
* Show the 70% refusal with a real bench supply or a native test, not an edited
  number.
* Keep the terminal font large enough to read at 1080p.
* Record a backup narration over the replay in case the hardware fails.

## 7. Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Hardware not ready or a node fails on the day | Medium | High | Replay is the default demo; live is the stretch |
| Relay or MOSFET damaged | Low | Medium | Spare IRLZ44N, 1N4007 and SRD-12VDC relay |
| Battery below 70% at demo time | Medium | Medium | Charge the night before; bench supply for the boundary test |
| Portal upload fails near the deadline | Low | High | Upload by 18:00 IST; keep a zip and a private video link |
| Reviewer challenges the simulated headline | High | Medium | Lead with `docs/LIMITATIONS.md`; never overclaim |
| `run_all.py` fails on the reviewer's machine | Low | Medium | CI quickstart job runs the same command on Ubuntu |
| Python 3.12 vs 3.11 package drift | Low | Low | CI uses 3.11; document the tested version |

## 8. Submission-day sequence

1. **09:00** — final `git pull`, `python scripts/run_all.py --quick`, confirm
   green.
2. **10:00** — record or finalise the video; watch it once end to end.
3. **12:00** — upload the write-up, video and repository link to YouNoodle.
4. **14:00** — verify the portal shows the submission as complete; download the
   confirmation.
5. **16:00** — optional buffer for fixes. Do not start new features.
6. **18:00** — stop. The remaining five hours are for portal problems, not code.

## 9. What "done" means

The submission is done when a reviewer can clone the repository, run
`python scripts/run_all.py --quick`, open the dashboard, read
`docs/LIMITATIONS.md`, and see exactly which claims are simulated, which are
tested and which are still bench-pending. Nothing in the package should require
a verbal footnote to be honest.
