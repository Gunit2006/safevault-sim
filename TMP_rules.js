// prototype/src/rules.js
// Configuration matching params.yaml
export const CONFIG = {
  everyday_cap: 500000,
  large_threshold: 50000,
  timelock_hours: 48,
  age_cutoff: 70,
  velocity_count: 3,
  velocity_window_hours: 24,
  trusted_person_response_minutes: 30
};

/**
 * Implements RULES.md evaluation logic
 * Actions: "ALLOW", "HOLD", "REJECT", "ESCALATE"
 *
 * @param {Object} tx - The transaction object
 * @param {Object} context - Contextual state (e.g. call active, velocity)
 * @returns {Object} { action, reason }
 */
export function evaluateSafeVault(tx, context) {
  // 1. SAFETY CHECKS (run first)
  if (context.isCallFlagged || context.onCall) {
    return { 
      action: "REJECT", 
      reason: "🚫 Suspicious call detected — blocked, family alerted" 
    };
  }

  if (context.velocity24h >= CONFIG.velocity_count) {
    return {
      action: "ESCALATE",
      reason: "⚠️ Escalate: Too many large transactions in 24h"
    };
  }

  // 2. VAULT RULES
  if (tx.account === 'vault') {
    return {
      action: "HOLD",
      reason: `🔒 Held ${CONFIG.timelock_hours}h. Bank will verify. Trusted person notified.`
    };
  }

  if (context.fdJustBroken) {
    return {
      action: "HOLD",
      reason: "🔒 Held: FD just broken. Bank will verify. Trusted person notified."
    };
  }

  // 4. EMERGENCY PATH (evaluated before generic payment rules to allow pre-approved fast)
  if (context.isEmergency) {
    if (context.payeePreapproved) {
      return {
        action: "ALLOW",
        reason: "✅ Payment sent (Fast path: Pre-approved emergency payee)"
      };
    } else {
      return {
        action: "HOLD",
        reason: "Trusted person notified to approve"
      };
    }
  }

  // 3. PAYMENT RULES (everyday account)
  if (tx.payeeType === 'individual' && tx.isNewPayee && tx.amount > CONFIG.large_threshold) {
    return {
      action: "HOLD",
      reason: "⚠️ Held for review"
    };
  }

  if (tx.channel === 'RTGS' && tx.isNewPayee && context.age >= CONFIG.age_cutoff && tx.amount > CONFIG.large_threshold) {
    return {
      action: "HOLD",
      reason: "⚠️ Held for review (Large RTGS to new payee)"
    };
  }

  // Known payee, within normal limit, or merchant light touch
  return {
    action: "ALLOW",
    reason: "✅ Payment sent"
  };
}
