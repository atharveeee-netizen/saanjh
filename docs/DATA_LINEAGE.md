# Data Lineage Audit

The following directed acyclic graph (DAG) represents the proven data lineage in the SAANJH ecosystem. The flow has been verified through structural code inspection and mutation testing.

```mermaid
graph TD
    A[config.py (Engineering Constraints)] --> B(feeder_sim.py)
    C[Real World Load Data] --> D(XGBoost Trainer)
    D --> E(real_xgboost_model.pkl)
    E --> B
    B --> F[feeder_profile.csv]
    B --> G[saanjh_profile.csv]
    F --> H(PyPSA Validator)
    G --> H
    H --> I[pypsa_validation.csv]
    F --> J(Metrics Engine)
    G --> J
    J --> K[comparison.json]
    K --> L[Dashboard app.py]
    G --> M(Blender Visualization Loader)
    M --> N[saanjh_visualization_data.json]
    N --> O(Blender animate_event.py)
    O --> P[Digital Twin MP4]
```

## Source of Truth Verification
- **Are results calculated manually?** NO. All outcomes are derived dynamically by the `feeder_sim.py` execution.
- **Does the dashboard consume intermediate results?** YES. The dashboard strictly reads `comparison.json` and the CSV profiles.
- **Does Blender execute independent physics?** NO. Blender's `animate_event.py` reads `saanjh_visualization_data.json` and maps it via handlers.

**STATUS: PASS**
