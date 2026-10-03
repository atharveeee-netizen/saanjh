# PyPSA-USA Patterns
**Scenario Architecture Study:**
PyPSA-USA separates data inputs from structural model definitions via strict configuration files (`config.yaml`).
* **Pattern worth adopting**: Moving `number_of_homes`, `transformer_limit`, and `battery_specs` strictly into a `saanjh.yaml` instead of keeping them in python constants.
* **Reject**: The heavy snakemake workflow (overkill for SAANJH).
