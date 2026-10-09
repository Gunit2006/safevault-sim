import pandas as pd

def verify_hold(transaction, params):
    """
    Verification Module — SEPARATE, SWAPPABLE SEAM
    Simulates the independent bank check or trusted person response.
    Returns: bool (True if verified/allowed, False if blocked)
    """
    # For simulation purposes, we can assume verification fails if coercion_active is True.
    # HOWEVER, the engine must NOT see coercion_active during decision making.
    # The scoring step will evaluate if a HOLD was successful.
    # For the batch runner, we just output the decision (e.g. HOLD).
    # The evaluation step will decide if a HOLD actually blocks fraud.
    pass


def decide(txn, params, policy="Integrated"):
    """
    Evaluates a transaction against SafeVault rules.
    policy options:
      - "B0": Always ALLOW
      - "B1": RBI rule (amount > 50k -> HOLD, else ALLOW)
      - "Integrated": Full rules
      - "Integrated_minus_safety": Full rules without safety checks
      - "Integrated_minus_vault": Full rules without vault rules
      - "Integrated_minus_emergency": Full rules without emergency path
    
    Returns: (action, reason_code)
      action in ["ALLOW", "HOLD", "REJECT", "ESCALATE"]
    """
    if policy == "B0":
        return "ALLOW", "B0_BASELINE"
        
    if policy == "B1":
        if txn["amount"] > params["rules"]["large_threshold"]:
            return "HOLD", "B1_RBI_RULE"
        return "ALLOW", "B1_BASELINE"
    
    # Flags for ablations
    use_safety = policy != "Integrated_minus_safety"
    use_vault = policy != "Integrated_minus_vault"
    use_emergency = policy != "Integrated_minus_emergency"

    # Tunable numbers
    rules = params["rules"]
    large_thresh = rules["large_threshold"]
    velocity_count = rules["velocity_count"]
    age_cutoff = rules["age_cutoff"]

    # 1. SAFETY CHECKS (run first)
    if use_safety:
        # Detect suspicious call
        if txn["call_origin"] in ["flagged", "international", "spoofed"] or txn.get("call_origin") == "domestic":
            # Wait, domestic is genuine call, not flagged.
            # Only flagged/international/spoofed are bad.
            if txn["call_origin"] in ["flagged", "international", "spoofed"]:
                return "REJECT", "SAFETY_CALL_DETECTED"
        
        if txn["velocity_24h"] >= velocity_count:
            return "ESCALATE", "SAFETY_VELOCITY"

    # 2. VAULT RULES
    if use_vault:
        if txn["is_vault_release"] or txn["account"] == "vault":
            return "HOLD", "VAULT_RELEASE"
        if txn["fd_just_broken"]:
            return "HOLD", "VAULT_FD_BROKEN"

    # 3. EMERGENCY PATH
    if use_emergency:
        if txn["is_emergency"]:
            if txn["payee_preapproved"]:
                return "ALLOW", "EMERGENCY_PREAPPROVED"
            else:
                return "HOLD", "EMERGENCY_UNLISTED"

    # 4. PAYMENT RULES
    # New INDIVIDUAL payee + large amount -> HOLD
    if txn["payee_type"] == "individual" and txn["payee_is_new"] and txn["amount"] > large_thresh:
        return "HOLD", "PAYMENT_NEW_INDIVIDUAL_LARGE"
        
    # Large RTGS to new payee (senior) -> HOLD
    if txn["channel"] == "RTGS" and txn["payee_is_new"] and txn["age"] >= age_cutoff and txn["amount"] > large_thresh:
        return "HOLD", "PAYMENT_LARGE_RTGS_NEW"

    return "ALLOW", "DEFAULT_ALLOW"
