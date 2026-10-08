# SafeVault — Decision Rules (v1, locked)

SafeVault is a protection module integrated into a bank's own app. Design assumes bank-level access: all channels (app, branch, RTGS), real account structure, and registered-contact verification are available.

## Core principle
No single tap and no phone can RELEASE vault money. Vault release needs TIME + an independent bank check. The victim is never required to act cleverly under stress — protection is structural.

## Accounts
- everyday — pension, income, daily spending. Normal channel limits apply. Cap Rs 5,00,000; any excess auto-sweeps into vault.
- vault — major savings + FDs. No instant digital transfer out.
- Business-owner seniors: registered vendors/staff form an approved-payee lane that flows freely; their protection leans on the vault wall + coercion signals rather than new-payee friction.

## Evaluation order (IMPORTANT)
Safety/coercion checks run FIRST. Nothing is fast-allowed while a coercion signal is active.

1. SAFETY CHECKS (run first)
   - Active call / screen-share detected, OR call from a flagged/international/spoofed number, during transfer (best-effort) → raise alert, run safety checks (REJECT/HOLD + family alert + bank check)
   - Velocity: 3+ large transfers in 24h → ESCALATE
   - Risk flag active on this payment → HOLD

2. VAULT RULES
   - Any vault release → HOLD 48h + independent bank check on a scammer-proof channel (registered number / video-KYC / branch). Check catches coercion → stop + alert family. Clean → release.
   - FD early closure (senior) → early-warning flag + HOLD (vault rules apply)

3. PAYMENT RULES (everyday account)
   - New INDIVIDUAL payee + large amount → HOLD + check
   - New MERCHANT payee → light touch; flag only if very large / brand-new
   - Known payee, within normal limit → ALLOW
   - Large RTGS to new payee (senior) → HOLD + check (all channels, via bank integration)

4. EMERGENCY PATH
   - Pre-approved payee (family, known hospital) → fast ALLOW
   - Emergency to UNLISTED payee → HOLD + instant trusted-person alert. Trusted person approves → release in minutes. No response in X min → bank fallback (video-check / continued hold).

## Trusted person
Can CANCEL / DELAY, and APPROVE release of the senior's own held payment (emergency path). NEVER redirects, initiates, or sends money. Sees only the pending payment (amount + payee), not balances.

## Actions
ALLOW · HOLD · REJECT · ESCALATE

## Tunable numbers (from params.yaml)
everyday cap (Rs 5L), Rs 50k large-threshold, time-lock hours (48 default; test 24/72), age cutoff (test 60/65/70), velocity count (3) & window (24h), trusted-person response window (X min).

## Honest limits (stated, not solved)
- OS limits on call/screen-share detection (best-effort only)
- Deepfakes on video checks
- A fully coached victim lying to the bank
- Cross-bank escape (scammer opens account at another bank) — needs RBI/NPCI network-level coordination (future scope)
