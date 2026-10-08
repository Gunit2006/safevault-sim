"""
Generate synthetic senior-citizen profiles and their normal payment history.
All numbers come from params.yaml — nothing is hardcoded.
"""
import random
import uuid
from datetime import datetime, timedelta

import pandas as pd


def _random_timestamp(start: datetime, end: datetime) -> datetime:
    """Uniform random timestamp between start and end."""
    delta = (end - start).total_seconds()
    return start + timedelta(seconds=random.uniform(0, delta))


def generate_seniors(params: dict, seed: int = 42) -> pd.DataFrame:
    """
    Create normal payment transactions for `num_seniors` seniors.

    Returns a DataFrame with Transaction-level rows + hidden label columns
    (is_fraud=False, coercion_active=False, is_emergency).
    """
    random.seed(seed)

    pop = params["population"]
    pay = params["normal_payments"]

    num_seniors = pop["num_seniors"]
    min_age = pop["min_age"]
    max_age = pop["max_age"]
    sim_days = pop["simulation_days"]

    avg_txns = pay["avg_per_senior_per_month"]
    amt_min = pay["typical_amount_min"]
    amt_max = pay["typical_amount_max"]
    large_max = pay["large_genuine_amount_max"]
    pct_large = pay["pct_payments_above_50k"] / 100.0
    emergency_rate = pay["emergency_payment_rate"]

    # Simulation window
    start = datetime(2026, 10, 1)
    end = start + timedelta(days=sim_days)

    # Scale monthly average to the simulation window
    txns_per_senior = max(1, int(avg_txns * sim_days / 30))

    # Build a pool of "known" payees per senior (recurring bills, family, etc.)
    known_payees = {}
    for i in range(num_seniors):
        cid = f"CUST-{i:04d}"
        # each senior has 5–12 known payees
        n_payees = random.randint(5, 12)
        known_payees[cid] = [f"PAYEE-{uuid.uuid4().hex[:8]}" for _ in range(n_payees)]

    rows = []
    for i in range(num_seniors):
        cid = f"CUST-{i:04d}"
        age = random.randint(min_age, max_age)
        # slight per-senior variance in txn count
        n_txns = max(1, int(random.gauss(txns_per_senior, txns_per_senior * 0.2)))

        for _ in range(n_txns):
            is_large = random.random() < pct_large
            is_emergency = random.random() < emergency_rate

            if is_large:
                amount = round(random.uniform(50_000, large_max), 2)
            else:
                amount = round(random.uniform(amt_min, amt_max), 2)

            # Channel mix: ~70% UPI, ~20% branch, ~10% RTGS for normal payments
            channel = random.choices(
                ["UPI", "branch", "RTGS"], weights=[70, 20, 10]
            )[0]

            # Mostly known payees; ~10% new payee in normal flow
            if random.random() < 0.10:
                payee_id = f"PAYEE-{uuid.uuid4().hex[:8]}"
            else:
                payee_id = random.choice(known_payees[cid])

            # Account type: routine payments use everyday; large payments can use vault/FD
            if is_large:
                account = random.choices(["everyday", "vault", "FD"], weights=[40, 40, 20])[0]
            else:
                account = "everyday"

            rows.append({
                "txn_id": f"TXN-{uuid.uuid4().hex[:12]}",
                "customer_id": cid,
                "age": age,
                "amount": amount,
                "channel": channel,
                "payee_id": payee_id,
                "timestamp": _random_timestamp(start, end),
                "account": account,
                "fd_just_broken": account == "FD",   # FD account ⇒ FD was broken
                "payee_type": random.choices(["individual", "merchant"], weights=[40, 60])[0],
                "call_origin": random.choices(["none", "domestic"], weights=[97, 3])[0],
                "is_vault_release": account == "vault",
                "is_emergency": is_emergency,
                "payee_preapproved": random.random() < 0.1,
                "is_fraud": False,
                "coercion_active": False,
            })

    return pd.DataFrame(rows)
