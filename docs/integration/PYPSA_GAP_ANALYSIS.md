# PyPSA Gap Analysis
* **CURRENT**: SAANJH uses a custom `feeder_sim.py` which aggregates load but lacks rigorous physical AC power-flow limits (specifically voltage drop/rise).
* **AVAILABLE**: PyPSA provides strict Newton-Raphson power flow and linear optimal power flow for constraints.
* **MISSING**: SAANJH's `pypsa_validator.py` currently only checks total active power balance, not bus-level voltage profiles during extreme dispatch events.
* **REQUIRED?**: YES. A robust hackathon submission must prove dispatch commands do not cause voltage collapse on the distribution grid.
