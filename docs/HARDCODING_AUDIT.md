# Hardcoding Forensics Audit

## 1. Search Methodology
An exhaustive structural search was conducted across all `.py`, `.js`, `.html`, `.md`, and `.json` files for known KPI literal values (e.g., peak reduction percentages, kw limits, specific time indices).

## 2. Findings
- **Dashboard (`app.py`):** The Streamlit dashboard strictly loads data from `simulation/data/results/comparison.json`, `baseline_profile.csv`, and `saanjh_profile.csv`. No static arrays or string KPIs exist.
- **Blender Pipeline (`animate_event.py`):** The Blender animation script consumes the simulation states directly from `saanjh_visualization_data.json` via a linear interpolation function. The state logic is strictly data-driven.
- **Submission Documents:** Markdown documents (like `README.md`) reference the dynamically generated metrics. Any numbers mentioned in `VOICEOVER_SCRIPT.md` represent static narrative framing (e.g., 60 homes) which are defined as canonical design constraints, not simulated KPIs.

## 3. Conclusion
The repository strictly adheres to the **"No Hardcoded Generated Results"** rule. All presented data flows deterministically from the upstream simulation engines.

**STATUS: PASS**
