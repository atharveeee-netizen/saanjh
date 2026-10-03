# Third-Party Components

| Component | Repository URL | License | Version/Commit | Files Reused | Original Copyright Retained? | SAANJH Modifications | Purpose |
|---|---|---|---|---|---|---|---|
| NREL Virtual Battery Aggregator (Architecture & Logic) | https://github.com/NREL/virtual-battery-aggregator | BSD-3-Clause | `main` | Extracted math & architecture from `aggregator/BatteryAggregator.py` | Yes | Rewritten in NumPy without `cvxpy` dependency to maintain CPU speed & exact SAANJH schema. | Provides the core logic for scaling household flexibility into a single Virtual Battery entity. |
| PyPSA (Python for Power System Analysis) | https://github.com/PyPSA/PyPSA | MIT | Latest (pip) | Used as an external PIP dependency | Yes (MIT License preserved in pip dist) | None (Used purely as an independent black-box validation module) | Independent electrical validation of SAANJH feeder and transformer simulation logic. |
