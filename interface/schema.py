"""
Shared contract between generator (my code) and policy engine (teammate's code).
DO NOT change field names — both sides depend on them.
"""
from dataclasses import dataclass, field
from datetime import datetime


# ── Observable fields the policy engine may read ─────────────────────
@dataclass
class Transaction:
    txn_id: str
    customer_id: str
    age: int
    amount: float
    channel: str          # "UPI" | "RTGS" | "branch"
    payee_id: str
    payee_is_new: bool
    timestamp: datetime
    account: str          # "everyday" | "vault" | "FD"
    velocity_24h: int
    fd_just_broken: bool


# ── Hidden truth labels — engine must NEVER see these ────────────────
@dataclass
class Labels:
    txn_id: str
    is_fraud: bool
    coercion_active: bool


# ── Decision the engine returns ──────────────────────────────────────
@dataclass
class Decision:
    txn_id: str
    action: str           # "ALLOW" | "HOLD" | "REJECT" | "ESCALATE"
    hold_hours: int
    reason_code: str
    policy_version: str
