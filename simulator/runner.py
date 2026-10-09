import os
import yaml
import pandas as pd
from simulator.engine import decide

def run_simulation(data_dir="data", results_dir="results", params_path="params.yaml"):
    with open(params_path, "r") as f:
        params = yaml.safe_load(f)
        
    txns = pd.read_csv(os.path.join(data_dir, "transactions.csv"))
    
    policies = [
        "B0", 
        "B1", 
        "Integrated",
        "Integrated_minus_safety",
        "Integrated_minus_vault",
        "Integrated_minus_emergency"
    ]
    
    # Store results in a list of dicts
    results = []
    
    # Convert dataframe to list of dicts for easier row-by-row processing
    txn_records = txns.to_dict("records")
    
    for txn in txn_records:
        row_result = {"txn_id": txn["txn_id"]}
        for policy in policies:
            action, reason = decide(txn, params, policy)
            row_result[f"{policy}_action"] = action
            row_result[f"{policy}_reason"] = reason
        results.append(row_result)
        
    res_df = pd.DataFrame(results)
    os.makedirs(results_dir, exist_ok=True)
    res_df.to_csv(os.path.join(results_dir, "decisions.csv"), index=False)
    print(f"✓ Simulation complete. Decisions saved to {results_dir}/decisions.csv")
    return res_df

if __name__ == "__main__":
    run_simulation()
