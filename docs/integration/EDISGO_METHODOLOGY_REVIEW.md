# eDisGo Methodology Review
**AGPL-3.0 WARNING: NO CODE COPIED**

1. **CONCEPT:** Over-voltage from excessive rooftop PV and under-voltage from EV/HVAC peaks.
   **WHY SAANJH NEEDS IT:** Virtual battery dispatch must not violate local bus voltage limits.
   **CURRENT SAANJH EQUIVALENT:** Total transformer KW loading check.
   **GAP:** Ignores topology and impedance; a node at the end of the feeder might face severe voltage drop even if total KW is fine.
   **POSSIBLE NATIVE IMPLEMENTATION:** Use PyPSA to build a radial line from the transformer. Assign loads to nodes. Run `network.pf()`. Check `network.buses_t.v_mag_pu`.
