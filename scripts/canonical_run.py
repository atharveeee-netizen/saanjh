import os
import sys
import json
import time
import subprocess
import hashlib

def run_canonical_pipeline():
    print("==================================================")
    print("   SAANJH CANONICAL PIPELINE EXECUTION (PHASE 32) ")
    print("==================================================")
    start_time = time.time()
    base_dir = os.path.dirname(os.path.dirname(__file__))
    
    # Step 1: Feeder Simulation & PyPSA AC Load Flow & Scorecard Generation
    print("\n[1/4] Running Feeder Simulation, Grid Physics & PyPSA Validation...")
    subprocess.run([sys.executable, os.path.join(base_dir, "simulation", "feeder_sim.py")], check=True)
    
    # Step 2: Monte Carlo & Invariant Checks
    print("\n[2/4] Running 50-Iteration Monte Carlo Robustness Validation...")
    subprocess.run([sys.executable, os.path.join(base_dir, "simulation", "run_monte_carlo.py")], check=True)
    
    # Step 3: Blender Visualization Data Sync
    print("\n[3/4] Exporting Data Contract for 3D Digital Twin...")
    subprocess.run([sys.executable, os.path.join(base_dir, "scripts", "generate_blender_data.py")], check=True)
    
    # Step 4: Documentation Compilation
    print("\n[4/4] Compiling README.md & docs/SUBMISSION.md from Live KPIs...")
    subprocess.run([sys.executable, os.path.join(base_dir, "scripts", "generate_docs.py")], check=True)
    
    total_duration = round(time.time() - start_time, 2)
    print(f"\n[CANONICAL PIPELINE COMPLETE] Total Execution Time: {total_duration}s")
    
    # Record CANONICAL_RUN.json
    res_dir = os.path.join(base_dir, "simulation", "data", "results")
    with open(os.path.join(res_dir, "comparison.json"), "r") as f:
        kpis = json.load(f)
        
    def hash_file(fpath):
        if not os.path.exists(fpath):
            return "MISSING"
        h = hashlib.sha256()
        with open(fpath, "rb") as fl:
            h.update(fl.read())
        return h.hexdigest()[:16]

    canonical_record = {
        "pipeline_name": "SAANJH Challenge 03 Canonical Pipeline",
        "execution_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "execution_duration_seconds": total_duration,
        "status": "PASS",
        "key_kpis": kpis,
        "artifact_hashes": {
            "comparison.json": hash_file(os.path.join(res_dir, "comparison.json")),
            "reliability_scorecard.json": hash_file(os.path.join(res_dir, "reliability_scorecard.json")),
            "pypsa_saanjh_validation.csv": hash_file(os.path.join(res_dir, "pypsa_saanjh_validation.csv")),
            "household_dispatch.csv": hash_file(os.path.join(res_dir, "household_dispatch.csv")),
            "flexibility_request.json": hash_file(os.path.join(res_dir, "flexibility_request.json")),
            "flexibility_response.json": hash_file(os.path.join(res_dir, "flexibility_response.json")),
            "saanjh_profile.csv": hash_file(os.path.join(res_dir, "saanjh_profile.csv")),
            "saanjh_visualization_data.json": hash_file(os.path.join(base_dir, "artifacts", "blender", "saanjh_visualization_data.json")),
            "saanjh_final_presentation.mp4": hash_file(os.path.join(base_dir, "artifacts", "video", "saanjh_final_presentation.mp4"))
        }
    }
    
    audit_dir = os.path.join(base_dir, "docs", "final_audit")
    os.makedirs(audit_dir, exist_ok=True)
    with open(os.path.join(audit_dir, "CANONICAL_RUN.json"), "w") as f:
        json.dump(canonical_record, f, indent=4)
        
    print(f"Recorded canonical run manifest to: {os.path.join(audit_dir, 'CANONICAL_RUN.json')}")

if __name__ == "__main__":
    run_canonical_pipeline()
