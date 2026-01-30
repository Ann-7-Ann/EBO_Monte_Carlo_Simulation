"""Deterministic RNG utilities.

We keep *all* Monte Carlo randomness behind a single Random instance so that
the simulation is reproducible given a fixed seed.
"""

from __future__ import annotations

import random


class RNGManager:
    def __init__(self, seed: int = 0):
        self._seed = int(seed)
        self._rng = random.Random(self._seed)

    @property
    def seed(self) -> int:
        return self._seed

    def set_seed(self, seed: int) -> None:
        self._seed = int(seed)
        self._rng = random.Random(self._seed)

    def rng(self) -> random.Random:
        return self._rng
