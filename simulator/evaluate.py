import os
import pandas as pd

def evaluate(data_dir="data", results_dir="results"):
    txns = pd.read_csv(os.path.join(data_dir, "transactions.csv"))
    labels = pd.read_csv(os.path.join(data_dir, "labels.csv"))
    decisions = pd.read_csv(os.path.join(results_dir, "decisions.csv"))
    
    # Merge all
    df = txns.merge(labels, on="txn_id").merge(decisions, on="txn_id")
    
    policies = [
        "B0", 
        "B1", 
        "Integrated",
        "Integrated_minus_safety",
        "Integrated_minus_vault",
        "Integrated_minus_emergency"
    ]
    
    BLOCK_ACTIONS = {"HOLD", "REJECT", "ESCALATE"}
    
    metrics = []
    
    for policy in policies:
        action_col = f"{policy}_action"
        
        # Fraud value blocked
        fraud_df = df[df["is_fraud"] == True]
        total_fraud_value = fraud_df["amount"].sum()
        blocked_fraud_value = fraud_df[fraud_df[action_col].isin(BLOCK_ACTIONS)]["amount"].sum()
        fraud_blocked_pct = (blocked_fraud_value / total_fraud_value * 100) if total_fraud_value > 0 else 0
        
        # Genuine delayed
        genuine_df = df[df["is_fraud"] == False]
        total_genuine = len(genuine_df)
        delayed_genuine = len(genuine_df[genuine_df[action_col].isin(BLOCK_ACTIONS)])
        genuine_delayed_pct = (delayed_genuine / total_genuine * 100) if total_genuine > 0 else 0
        
        # Emergencies failed (count of genuine emergencies that were blocked)
        # HELD emergencies are resolved via the trusted-person path, so they are not failures.
        # Only outright REJECTED or ESCALATED emergencies count as failed.
        emergencies = genuine_df[genuine_df["is_emergency"] == True]
        emergencies_failed = len(emergencies[emergencies[action_col].isin(["REJECT", "ESCALATE"])])
        
        metrics.append({
            "Policy": policy,
            "Fraud Value Blocked (%)": round(fraud_blocked_pct, 2),
            "Genuine Delayed (%)": round(genuine_delayed_pct, 2),
            "Emergencies Failed (Count)": emergencies_failed
        })
        
    metrics_df = pd.DataFrame(metrics)
    os.makedirs(results_dir, exist_ok=True)
    out_path = os.path.join(results_dir, "comparison.csv")
    metrics_df.to_csv(out_path, index=False)
    
    print("\n=== SafeVault Simulator Results ===")
    print(metrics_df.to_string(index=False))
    print(f"\nSaved to {out_path}")
    
    return metrics_df

if __name__ == "__main__":
    evaluate()
