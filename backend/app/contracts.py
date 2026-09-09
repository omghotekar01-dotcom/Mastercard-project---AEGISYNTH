"""Shared safety contracts for policy feature domains.

These constants are consumed by both schema validation and formal verification so
judge-facing policy evidence cannot be accepted under different numeric domains.
"""

POLICY_MERCHANT_AGE_HOURS_MIN = 0.0
POLICY_MERCHANT_AGE_HOURS_MAX = float(24 * 365 * 20)
POLICY_FIRST_TIME_CARD_RATIO_MIN = 0.0
POLICY_FIRST_TIME_CARD_RATIO_MAX = 1.0
POLICY_SETTLEMENT_CHANGE_DAYS_MIN = 0.0
POLICY_SETTLEMENT_CHANGE_DAYS_MAX = 3650.0
POLICY_TEMPORAL_BURST_SCORE_MIN = 0.0
POLICY_TEMPORAL_BURST_SCORE_MAX = 1.0
