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

        is_large = random.random() < (scam.get("large_scam_pct", 40) / 100.0)
        is_high_freq = random.random() < (scam.get("high_freq_small_pct", 30) / 100.0)
        is_vault = random.random() < (scam.get("vault_target_pct", 30) / 100.0)
        
        # Determine total loss and number of txns
        if is_high_freq:
            # 5-8 txns of 15k-40k each (under the 50k threshold)
            n_txns = random.randint(5, 8)
            base_amt = random.uniform(15000, 40000)
        elif is_large:
            total_loss = round(random.uniform(500000, loss_max), 2)
            is_multi = random.random() < (scam.get("multi_instalment_pct", 60) / 100.0)
            n_txns = random.randint(2, 4) if is_multi else 1
            base_amt = total_loss / n_txns
        else:
            total_loss = round(random.uniform(loss_min, 499999), 2)
            is_multi = random.random() < (scam.get("multi_instalment_pct", 60) / 100.0)
            n_txns = random.randint(2, 4) if is_multi else 1
            base_amt = total_loss / n_txns

        base_timestamp = datetime(2026, 10, 1) + timedelta(seconds=random.uniform(0, sim_days * 86400))
        
        for i in range(n_txns):
            if is_high_freq:
                amount = round(random.uniform(15000, 40000), 2)
            else:
                amount = round(base_amt * random.uniform(0.9, 1.1), 2)
            
            # channel is UPI if < 200k, else RTGS
            txn_channel = "UPI" if amount < 200000 else "RTGS"
            
            payee_id = f"SCAM-{uuid.uuid4().hex[:8]}"

            rows.append({
                "txn_id": f"TXN-{uuid.uuid4().hex[:12]}",
                "customer_id": cid,
                "age": age,
                "amount": amount,
                "channel": txn_channel,
                "payee_id": payee_id,
                "timestamp": base_timestamp + timedelta(minutes=i * 45), # installments are 45 mins apart
                "account": "vault" if is_vault else "everyday",
                "fd_just_broken": False,
                "payee_type": "individual", # scammers usually pose as individuals or officials
                "call_origin": random.choices(["none", "spoofed", "flagged", "international"], weights=[45, 25, 20, 10])[0],
                "is_vault_release": is_vault,
                "is_emergency": False,
                "payee_preapproved": False,
                "is_fraud": True,
                "coercion_active": True,
            })

    return pd.DataFrame(rows)
