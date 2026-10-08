"""
Combine normal + scam transactions into a single stream, compute derived
fields (velocity_24h, payee_is_new), and write the two output CSVs:

  data/transactions.csv  — observable fields only (engine reads this)
  data/labels.csv        — hidden truth (generator owns, engine never reads)
"""
import os

import pandas as pd
import yaml


def _compute_velocity(df: pd.DataFrame) -> pd.Series:
    """For each row, count how many prior txns that customer had in the last 24 h."""
    df = df.sort_values("timestamp").reset_index(drop=True)
    velocities = []
    for idx, row in df.iterrows():
        cid = row["customer_id"]
        ts = row["timestamp"]
        window_start = ts - pd.Timedelta(hours=24)
        # Count prior txns for same customer within 24 h window
        prior = df[
            (df["customer_id"] == cid)
            & (df["timestamp"] >= window_start)
            & (df["timestamp"] < ts)
        ]
        velocities.append(len(prior))
    return pd.Series(velocities, index=df.index)


def _compute_payee_is_new(df: pd.DataFrame) -> pd.Series:
    """True if the customer has never transacted with this payee before this txn."""
    df = df.sort_values("timestamp").reset_index(drop=True)
    seen = {}   # (customer_id, payee_id) → earliest timestamp
    flags = []
    for _, row in df.iterrows():
        key = (row["customer_id"], row["payee_id"])
        if key not in seen:
            flags.append(True)
            seen[key] = row["timestamp"]
        else:
            flags.append(False)
    return pd.Series(flags, index=df.index)


def build_stream(normal_df: pd.DataFrame, scam_df: pd.DataFrame) -> pd.DataFrame:
    """Merge, sort, compute derived fields, return full dataframe."""
    combined = pd.concat([normal_df, scam_df], ignore_index=True)
    combined = combined.sort_values("timestamp").reset_index(drop=True)

    # Derived observable fields
    combined["velocity_24h"] = _compute_velocity(combined)
    combined["payee_is_new"] = _compute_payee_is_new(combined)

    return combined


# ── Observable columns the engine is allowed to see ──────────────────
TRANSACTION_COLS = [
    "txn_id", "customer_id", "age", "amount", "channel",
    "payee_id", "payee_is_new", "timestamp", "account",
    "velocity_24h", "fd_just_broken", "payee_type",
    "call_origin", "is_vault_release", "is_emergency",
    "payee_preapproved",
]

# ── Hidden label columns ─────────────────────────────────────────────
LABEL_COLS = ["txn_id", "is_fraud", "coercion_active"]


def write_csvs(df: pd.DataFrame, data_dir: str = "data") -> None:
    """Split the full dataframe into transactions.csv and labels.csv."""
    os.makedirs(data_dir, exist_ok=True)

    txn_path = os.path.join(data_dir, "transactions.csv")
    lbl_path = os.path.join(data_dir, "labels.csv")

    df[TRANSACTION_COLS].to_csv(txn_path, index=False)
    df[LABEL_COLS].to_csv(lbl_path, index=False)

    print(f"✓ Wrote {len(df)} transactions → {txn_path}")
    print(f"✓ Wrote {len(df)} labels       → {lbl_path}")


# ── Convenience runner ───────────────────────────────────────────────
def run(params_path: str = "params.yaml", data_dir: str = "data") -> pd.DataFrame:
    """End-to-end: load params → generate normals → inject scams → write CSVs."""
    from generator.seniors import generate_seniors
    from generator.scams import inject_scams

    with open(params_path) as f:
        params = yaml.safe_load(f)

    normal = generate_seniors(params)
    scams = inject_scams(normal, params)
    full = build_stream(normal, scams)
    write_csvs(full, data_dir)
    return full


if __name__ == "__main__":
    run()
