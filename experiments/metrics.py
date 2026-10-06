"""
Scoring module: compare the policy engine's decisions against the hidden
truth labels and produce one summary row per policy version.

Key metrics:
  fraud_value_blocked_pct  — scam money HOLD/REJECT/ESCALATE ÷ total scam money
  genuine_delayed_pct      — genuine payments HOLD/REJECT ÷ total genuine
  emergencies_failed       — emergency genuine payments that were blocked
"""
import os

import pandas as pd


BLOCK_ACTIONS = {"HOLD", "REJECT", "ESCALATE"}   # actions that stop money
DELAY_ACTIONS = {"HOLD", "REJECT"}                # actions that inconvenience genuine users


def score(
    decisions_df: pd.DataFrame,
    labels_df: pd.DataFrame,
    full_df: pd.DataFrame,
    results_dir: str = "results",
) -> pd.DataFrame:
    """
    Score one policy run.

    Args:
        decisions_df: Decision rows from the engine (txn_id, action, ...).
        labels_df:    Hidden labels (txn_id, is_fraud, coercion_active).
        full_df:      Full transaction data (needs is_emergency flag for
                      emergency-failure counting).  May be the generator's
                      internal dataframe or the transactions CSV enriched
                      with the is_emergency column.
        results_dir:  Where to write the result CSV.

    Returns:
        One-row DataFrame with the metrics.
    """
    # Merge decisions with labels
    merged = decisions_df.merge(labels_df, on="txn_id", how="inner")

    # Attach amount + emergency flag
    amount_cols = full_df[["txn_id", "amount", "is_emergency"]].copy()
    merged = merged.merge(amount_cols, on="txn_id", how="left")

    # ── Fraud value blocked ──────────────────────────────────────────
    fraud_rows = merged[merged["is_fraud"] == True]
    total_scam_value = fraud_rows["amount"].sum()
    blocked_scam_value = fraud_rows[fraud_rows["action"].isin(BLOCK_ACTIONS)]["amount"].sum()
    fraud_blocked_pct = (
        (blocked_scam_value / total_scam_value * 100) if total_scam_value > 0 else 0.0
    )

    # ── Genuine payments delayed ─────────────────────────────────────
    genuine_rows = merged[merged["is_fraud"] == False]
    total_genuine = len(genuine_rows)
    delayed_genuine = len(genuine_rows[genuine_rows["action"].isin(DELAY_ACTIONS)])
    genuine_delayed_pct = (
        (delayed_genuine / total_genuine * 100) if total_genuine > 0 else 0.0
    )

    # ── Emergencies failed ───────────────────────────────────────────
    emergency_rows = genuine_rows[genuine_rows["is_emergency"] == True]
    emergencies_failed = len(
        emergency_rows[emergency_rows["action"].isin(BLOCK_ACTIONS)]
    )

    # ── Assemble result row ──────────────────────────────────────────
    policy_version = decisions_df["policy_version"].iloc[0] if len(decisions_df) > 0 else "unknown"
    result = pd.DataFrame([{
        "policy_version": policy_version,
        "total_transactions": len(merged),
        "total_scam_value": round(total_scam_value, 2),
        "fraud_value_blocked_pct": round(fraud_blocked_pct, 2),
        "total_genuine": total_genuine,
        "genuine_delayed_pct": round(genuine_delayed_pct, 2),
        "emergencies_failed": emergencies_failed,
    }])

    # Write to results/
    os.makedirs(results_dir, exist_ok=True)
    out_path = os.path.join(results_dir, f"result_{policy_version}.csv")
    result.to_csv(out_path, index=False)
    print(f"✓ Scored policy '{policy_version}' → {out_path}")

    return result
