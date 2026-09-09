"""Shared safety contracts for policy feature and compiler domains.

These constants are consumed across schema validation, benchmark execution, scoring,
and formal verification so judge-facing evidence cannot be accepted under different
numeric or compiler-generation domains.
"""

COMPILER_GENERATION_MIN = 1
COMPILER_GENERATION_MAX = 8
DEFAULT_MAX_FALSE_POSITIVE_RATE = 0.02

POLICY_MERCHANT_AGE_HOURS_MIN = 0.0
POLICY_MERCHANT_AGE_HOURS_MAX = float(24 * 365 * 20)
POLICY_FIRST_TIME_CARD_RATIO_MIN = 0.0
POLICY_FIRST_TIME_CARD_RATIO_MAX = 1.0
POLICY_SETTLEMENT_CHANGE_DAYS_MIN = 0.0
POLICY_SETTLEMENT_CHANGE_DAYS_MAX = 3650.0
POLICY_TEMPORAL_BURST_SCORE_MIN = 0.0
POLICY_TEMPORAL_BURST_SCORE_MAX = 1.0
