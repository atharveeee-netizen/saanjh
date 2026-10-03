# SAANJH Repository Inventory & Architecture Map

## 1. Directory Structure

```
saanjh/
├── artifacts/                  # Generated models, data, and video deliverables
│   ├── blender/                # Procedural visual metadata and audit logs
│   │   ├── BLENDER_DATA_AUDIT.md
│   │   └── saanjh_visualization_data.json
│   ├── models/                 # Serialized ML forecasting models
│   │   ├── real_baseline_model.pkl
│   │   └── real_xgboost_model.pkl
│   ├── real_data/              # Dataset manifests, forecasts, and training audits
│   │   ├── dataset_manifest.json
│   │   ├── forecasts.csv
│   │   └── model_comparison.json
│   └── video/                  # Presentation and digital twin video artifacts
│       ├── dashboard_recording.webm
│       ├── saanjh_digital_twin_preview.mp4
│       └── saanjh_final_presentation.mp4  # Master stitched video deliverable
├── blender/scripts/            # Procedural Blender 3D environment & HUD scripts
│   ├── animate_event.py        # Numerical driver binding simulation to 3D scene
│   ├── build_env.py            # Procedural feeder, transformer, and home assets
│   └── build_ui.py             # Isometric camera HUD anchored interface
├── config/                     # System configuration
│   └── saanjh.yaml             # Single source of truth for transformer & neighborhood parameters
├── docs/                       # Architectural documentation, diagrams & audits
│   ├── diagrams/               # High-resolution architectural figures & slide assets
│   ├── integration/            # Baseline snapshots and external methodology reviews
│   ├── BLENDER_ANIMATION_AUDIT.md
│   ├── FORENSIC_VERIFICATION_MASTER.md
│   ├── SUBMISSION.md           # Formal 10-slide written presentation deck
│   └── SUBMISSION_READINESS.md
├── scripts/                    # Automation, mutation testing, and compilation utilities
│   ├── compile_final_presentation.py
│   ├── freeze_baseline.py
│   ├── mutation_test.py
│   └── record_dashboard.py
├── simulation/                 # Physical grid, battery, and dispatch simulation engine
│   ├── config.py               # YAML-backed runtime configuration loader
│   ├── economics_engine.py     # DISCOM & household financial return model
│   ├── feeder_sim.py           # Core time-series feeder and transformer simulator
│   ├── run_adversarial_tests.py# Edge-case and physical safety validator
│   ├── run_monte_carlo.py      # Statistical robustness under stochastic load
│   ├── validators/             # PyPSA external grid power flow validator
│   └── virtual_battery/        # Aggregated battery capacity and SOC tracking
├── tests/                      # Pytest unit & regression tests
│   └── test_model_reload.py    # Model deserialization and inference safety
├── README.md                   # Primary project overview and judging guide
└── requirements.txt            # Python dependencies
```

## 2. Key Modules & Responsibilities

- **`config/saanjh.yaml` & `simulation/config.py`:** Centralizes all engineering constants (100 kVA transformer rating, 60 homes, 70% battery penetration, 230V nominal, load profile definitions) into a declarative YAML structure.
- **`simulation/feeder_sim.py`:** Mathematical time-step model calculating aggregate load, voltage drops along the feeder, transformer winding temperature, and coordinating battery discharge/deferral events.
- **`simulation/virtual_battery/`:** Aggregates individual 150Ah/12V lead-acid and lithium inverter systems into a unified dispatchable virtual battery bank while respecting reserve constraints (70% emergency blackout reserve).
- **`blender/scripts/`:** Procedural Blender Python scripts creating a cinematic 3D digital twin of the neighborhood grid with a camera-anchored telemetry HUD.
- **`scripts/compile_final_presentation.py`:** Stitches the physical hardware demonstration, the Streamlit dashboard session, and the 3D Blender digital twin into the final MP4 presentation (`saanjh_final_presentation.mp4`).
