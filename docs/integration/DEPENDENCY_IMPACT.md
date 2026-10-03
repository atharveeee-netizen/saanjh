# Dependency Impact Analysis
* **PyPSA:** Already installed. Impact: 0.
* **eDisGo:** AGPL. Substantial dependency footprint (pandapower, networkx, sqlalchemy). **Impact:** Unacceptable license and bloat. **Decision:** REJECT installation.
* **Py-Microgrid:** Requires HOPP, Pyomo, solvers. **Impact:** Massive footprint. **Decision:** REJECT.

**Conclusion:** Zero new dependencies are strictly required to improve voltage validation natively using existing PyPSA.
