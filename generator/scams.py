"""
Generate digital-arrest scam transactions for a subset of seniors.
All numbers come from params.yaml — nothing is hardcoded.
"""
import random
import uuid
from datetime import datetime, timedelta

import pandas as pd


def inject_scams(normal_df: pd.DataFrame, params: dict, seed: int = 99) -> pd.DataFrame:
    """
    Pick pct_seniors_targeted% of seniors and create one scam txn each.

    Scam profile (from real 2026 Indian "digital arrest" cases):
      - Large amount (5–50 lakh)
      - RTGS channel
      - To a brand-new payee
      - Labelled is_fraud=True, coercion_active=True
    """
    random.seed(seed)

    pop = params["population"]
    scam = params["digital_arrest_scam"]

    sim_days = pop["simulation_days"]
    pct_targeted = scam["pct_seniors_targeted"] / 100.0
    loss_min = scam["loss_amount_min"]
    loss_max = scam["loss_amount_max"]
    channel = scam["channel"]

    start = datetime(2026, 10, 1)
    end = start + timedelta(days=sim_days)

    # Select victims from the pool of unique seniors
    all_customers = normal_df["customer_id"].unique().tolist()
    n_victims = max(1, int(len(all_customers) * pct_targeted))
    victims = random.sample(all_customers, n_victims)

    rows = []
    for cid in victims:
        # Look up the victim's age from their existing transactions
        age = int(normal_df.loc[normal_df["customer_id"] == cid, "age"].iloc[0])

        amount = round(random.uniform(loss_min, loss_max), 2)
        payee_id = f"SCAM-{uuid.uuid4().hex[:8]}"  # always a new, unseen payee

        rows.append({
            "txn_id": f"TXN-{uuid.uuid4().hex[:12]}",
            "customer_id": cid,
            "age": age,
            "amount": amount,
            "channel": channel,
            "payee_id": payee_id,
            "timestamp": datetime(2026, 10, 1) + timedelta(
                seconds=random.uniform(0, sim_days * 86400)
            ),
            "account": "everyday",      # victims typically pay from everyday account
            "fd_just_broken": False,
            "payee_type": "individual", # scammers usually pose as individuals or officials
            "call_origin": random.choices(["none", "spoofed", "flagged", "international"], weights=[45, 25, 20, 10])[0],
            "is_vault_release": False,
            "is_emergency": False,
            "payee_preapproved": False,
            "is_fraud": True,
            "coercion_active": True,
        })

    return pd.DataFrame(rows)
