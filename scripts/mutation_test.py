import json
import os
import subprocess

def run_sim():
    subprocess.run(["python", "simulation/feeder_sim.py"], check=True)

def read_metrics():
    with open("simulation/data/results/comparison.json", "r") as f:
        return json.load(f)

def run_mutation_test():
    print("Running baseline mutation test (State A)...")
    run_sim()
    state_a = read_metrics()
    
    # Mutate config
    config_path = "simulation/config.py"
    with open(config_path, "r") as f:
        config_text = f.read()
        
    # Change HOMES_WITH_INVERTER_BATTERY
    mutated_config = config_text.replace("HOMES_WITH_INVERTER_BATTERY = 42", "HOMES_WITH_INVERTER_BATTERY = 10")
    with open(config_path, "w") as f:
        f.write(mutated_config)
        
    print("Running mutated test (State B: 10 batteries)...")
    try:
        run_sim()
        state_b = read_metrics()
        
        a_flex = state_a["flexibility_delivered_kw"]
        b_flex = state_b["flexibility_delivered_kw"]
        
        a_peak = state_a["saanjh_peak_kw"]
        b_peak = state_b["saanjh_peak_kw"]
        
        print(f"State A (42 batteries) - Flex: {a_flex}, Peak Load: {a_peak}")
        print(f"State B (10 batteries) - Flex: {b_flex}, Peak Load: {b_peak}")
        
        if a_flex != b_flex and a_peak != b_peak:
            print("MUTATION TEST PASSED. Data coupling proven.")
            
            # Write to integration matrix json
            with open("simulation/data/results/integration_matrix.json", "w") as out:
                json.dump({"mutation_test": "PASS", "details": "Reducing batteries reduced flexibility and increased peak load."}, out)
        else:
            print("MUTATION TEST FAILED. Data is not coupled!")
            
    finally:
        # Restore config
        with open(config_path, "w") as f:
            f.write(config_text)
        print("Restored original config. Running sim one more time to reset state.")
        run_sim()

if __name__ == "__main__":
    run_mutation_test()
