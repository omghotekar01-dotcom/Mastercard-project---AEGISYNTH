from __future__ import annotations
import math
import random
from .schemas import Transaction


def _require_positive_count(name: str, value: object) -> int:
    """Reject invalid sample sizes before synthetic-world state can advance."""
    if type(value) is not int or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _require_finite_hardness(value: object) -> float:
    """Reject non-numeric or non-finite mutation inputs before benchmark RNG state advances."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("hardness must be a finite number")
    return float(value)


class PaymentWorld:
    """Deterministic synthetic payment world; no real cardholder or merchant data is used."""

    def __init__(self, seed: int = 42):
        if type(seed) is not int:
            raise ValueError("seed must be an integer")
        self.rng = random.Random(seed)
        self._benign_seq = 0
        self._attack_seq = 0

    def _clip(self, x: float, lo: float = 0.0, hi: float = 1.0) -> float:
        return max(lo, min(hi, x))

    def benign(self, n: int = 1200) -> list[Transaction]:
        n = _require_positive_count("benign sample count", n)
        rows: list[Transaction] = []
        start = self._benign_seq
        for i in range(n):
            # Most benign merchants are mature; a minority are legitimate new/high-growth merchants.
            startup = self.rng.random() < 0.055
            rows.append(Transaction(
                tx_id=f"B-{start + i:06d}",
                amount=max(20, self.rng.lognormvariate(6.0 if not startup else 6.5, 0.7)),
                merchant_age_hours=max(1, self.rng.gauss(24 * (420 if not startup else 5.5), 24 * (260 if not startup else 3.5))),
                first_time_card_ratio=self._clip(self.rng.betavariate(2.0, 6.0) if not startup else self.rng.betavariate(4.0, 3.3)),
                settlement_change_days=max(0, self.rng.gauss(150, 100) if not startup else self.rng.gauss(24, 18)),
                temporal_burst_score=self._clip(self.rng.betavariate(1.5, 5.5) if not startup else self.rng.betavariate(3.0, 3.4)),
                device_entropy=self._clip(self.rng.betavariate(2.5, 4.0)),
                geo_velocity=max(0, self.rng.gauss(10, 15)),
                label=0,
            ))
        self._benign_seq += len(rows)
        return rows

    def attack(self, n: int = 500, family: str = "ghost_merchant_swarm", hardness: float = 0.0) -> list[Transaction]:
        """Generate a safe, fictional attack family. Hardness mutates values toward benign ranges."""
        n = _require_positive_count("attack sample count", n)
        h = self._clip(_require_finite_hardness(hardness))
        rows: list[Transaction] = []
        start = self._attack_seq
        for i in range(n):
            rows.append(Transaction(
                tx_id=f"A-{start + i:06d}",
                amount=max(50, self.rng.lognormvariate(7.4 - 0.25*h, 0.55)),
                merchant_age_hours=max(1, self.rng.gauss(42 + 70*h, 20 + 25*h)),
                first_time_card_ratio=self._clip(self.rng.gauss(0.86 - 0.23*h, 0.08 + 0.02*h)),
                settlement_change_days=max(0, self.rng.gauss(4 + 18*h, 4 + 4*h)),
                temporal_burst_score=self._clip(self.rng.gauss(0.89 - 0.24*h, 0.07 + 0.03*h)),
                device_entropy=self._clip(self.rng.gauss(0.78 - 0.18*h, 0.12)),
                geo_velocity=max(0, self.rng.gauss(90 - 25*h, 35)),
                label=1,
                attack_family=family,
            ))
        self._attack_seq += len(rows)
        return rows

    def calibration_set(self, benign_n: int = 1200, attack_n: int = 500, hardness: float = 0.0):
        # Validate all inputs before generating either population so a rejected call cannot
        # partially consume RNG state and break retry reproducibility.
        _require_positive_count("benign sample count", benign_n)
        _require_positive_count("attack sample count", attack_n)
        _require_finite_hardness(hardness)
        return self.benign(benign_n), self.attack(attack_n, hardness=hardness)
