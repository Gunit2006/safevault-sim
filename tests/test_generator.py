"""
Pytest checks for the generator output.

Run:  pytest tests/test_generator.py -v
"""
import os

import pandas as pd
import pytest
import yaml

from generator.stream import run, TRANSACTION_COLS, LABEL_COLS

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
PARAMS_PATH = os.path.join(os.path.dirname(__file__), "..", "params.yaml")


@pytest.fixture(scope="module")
def generated_data():
    """Run the generator once for all tests in this module."""
    full_df = run(params_path=PARAMS_PATH, data_dir=DATA_DIR)
    txn_df = pd.read_csv(os.path.join(DATA_DIR, "transactions.csv"))
    lbl_df = pd.read_csv(os.path.join(DATA_DIR, "labels.csv"))
    with open(PARAMS_PATH) as f:
        params = yaml.safe_load(f)
    return full_df, txn_df, lbl_df, params


# ── 1. transactions.csv has all Transaction columns ──────────────────
def test_transaction_columns(generated_data):
    _, txn_df, _, _ = generated_data
    for col in TRANSACTION_COLS:
        assert col in txn_df.columns, f"Missing column: {col}"


# ── 2. labels.csv has no overlap with transactions except txn_id ─────
def test_label_no_overlap(generated_data):
    _, txn_df, lbl_df, _ = generated_data
    txn_cols = set(txn_df.columns)
    lbl_cols = set(lbl_df.columns)
    overlap = txn_cols & lbl_cols
    assert overlap == {"txn_id"}, (
        f"Labels share non-txn_id columns with transactions: {overlap - {'txn_id'}}"
    )


# ── 3. Scam transactions exist and are large + RTGS + new payee ──────
def test_scam_properties(generated_data):
    full_df, txn_df, lbl_df, params = generated_data

    scam_cfg = params["digital_arrest_scam"]

    # Merge to identify scam rows in the transaction file
    fraud_ids = set(lbl_df[lbl_df["is_fraud"] == True]["txn_id"])
    assert len(fraud_ids) > 0, "No scam transactions generated"

    scam_txns = txn_df[txn_df["txn_id"].isin(fraud_ids)]

    for _, row in scam_txns.iterrows():
        assert row["amount"] >= scam_cfg["loss_amount_min"], (
            f"Scam amount {row['amount']} below minimum {scam_cfg['loss_amount_min']}"
        )
        assert row["channel"] == scam_cfg["channel"], (
            f"Scam channel should be {scam_cfg['channel']}, got {row['channel']}"
        )
        assert row["payee_is_new"] == True, "Scam payee should be new"


# ── 4. Label counts match expected scam rate ─────────────────────────
def test_scam_rate(generated_data):
    _, txn_df, lbl_df, params = generated_data

    pop = params["population"]
    scam_cfg = params["digital_arrest_scam"]

    expected_victims = max(1, int(pop["num_seniors"] * scam_cfg["pct_seniors_targeted"] / 100))
    actual_frauds = int(lbl_df["is_fraud"].sum())

    # Each victim gets exactly one scam txn
    assert actual_frauds == expected_victims, (
        f"Expected {expected_victims} scam txns, got {actual_frauds}"
    )


# ── 5. Row counts are reasonable ─────────────────────────────────────
def test_row_counts(generated_data):
    _, txn_df, lbl_df, params = generated_data

    pop = params["population"]
    pay = params["normal_payments"]

    # transactions.csv and labels.csv should have the same number of rows
    assert len(txn_df) == len(lbl_df), "Row count mismatch between CSVs"

    # Rough expected normal txns: 100 seniors × 20 txns/month × 1 month = ~2000
    expected_normal = pop["num_seniors"] * pay["avg_per_senior_per_month"]
    total = len(txn_df)
    # Allow ±40% tolerance because of Gaussian variance
    assert total > expected_normal * 0.6, f"Too few rows: {total}"
    assert total < expected_normal * 1.5, f"Too many rows: {total}"
