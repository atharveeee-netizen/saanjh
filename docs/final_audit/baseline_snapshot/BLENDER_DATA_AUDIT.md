# Blender Digital Twin Data Audit

## Files Inspected
- `scripts/generate_blender_data.py`
- `blender/scripts/animate_event.py`

## Findings
**No simulation outcomes or engineering thresholds are hardcoded in the Blender rendering scripts.** 

### Data Contract Enforcement
The visualization pipeline enforces a strictly one-way data flow:
1. `simulation/feeder_sim.py` generates the primary simulation results (`saanjh_profile.csv`).
2. `scripts/generate_blender_data.py` consumes this CSV and generates a unified, machine-readable JSON data contract at `artifacts/blender/saanjh_visualization_data.json`.
3. `blender/scripts/animate_event.py` parses the JSON file and binds the variables to animation keyframes.

### Variables Evaluated:
| Constant/Variable | Source | Justification | Action |
|---|---|---|---|
| `num_homes` | `saanjh_visualization_data.json` | The digital twin topology matches the simulation exactly. | Dynamic loading confirmed. |
| `transformer_stress` | `saanjh_visualization_data.json` | Extracted from simulation `Transformer_Loading_%` exceeding the physical 85% safety threshold. | Drives the redness of the Transformer Base Color via keyframes. |
| `flexibility_delivered_kw` | `saanjh_visualization_data.json` | Direct simulation output representing instantaneous dispatch power. | Drives the Emission Strength of the battery materials. |
| `radius = 30` | `animate_event.py` | Visual spacing constant for creating the neighbourhood ring. | Legitimate Visual Constant. |
| `1.0 sec = 1 timestep` | `generate_blender_data.py` | Defines animation speed. (Simulation interval is 5 min). | Legitimate Visual Constant. |

### Verification Status
The Blender animation is verified as a 100% data-driven visualization of the engineering model. 
No fabricated results are present in the rendering pipeline.
