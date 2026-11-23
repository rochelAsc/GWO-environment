"""Small, dependency-free Mamdani controller for adaptive GWO exploration."""
from __future__ import annotations

import numpy as np


def _trimf(x: np.ndarray, abc: tuple[float, float, float]) -> np.ndarray:
    a, b, c = abc
    left = np.zeros_like(x, dtype=float) if b == a else (x - a) / (b - a)
    right = np.zeros_like(x, dtype=float) if c == b else (c - x) / (c - b)
    return np.maximum(0.0, np.minimum(np.minimum(left, right), 1.0))


def _trapmf(x: np.ndarray, abcd: tuple[float, float, float, float]) -> np.ndarray:
    a, b, c, d = abcd
    rising = np.ones_like(x, dtype=float) if a == b else (x - a) / (b - a)
    falling = np.ones_like(x, dtype=float) if c == d else (d - x) / (d - c)
    return np.maximum(0.0, np.minimum(np.minimum(rising, falling), 1.0))


class MamdaniGWOController:
    """Map diversity and stagnation in [0, 1] to an exploration multiplier."""

    # Rows: diversity low/medium/high; columns: stagnation low/medium/high.
    # Output labels: 0=low, 1=medium, 2=high exploration.
    RULES = (
        (1, 2, 2),
        (0, 1, 2),
        (0, 1, 2),
    )

    def __init__(self, resolution: int = 501) -> None:
        if resolution < 101:
            raise ValueError("resolution must be at least 101")
        self.universe = np.linspace(0.5, 1.5, resolution)
        self.output_memberships = (
            _trapmf(self.universe, (0.5, 0.5, 0.68, 0.95)),
            _trimf(self.universe, (0.75, 1.0, 1.25)),
            _trapmf(self.universe, (1.05, 1.32, 1.5, 1.5)),
        )

    @staticmethod
    def _input_memberships(value: float) -> tuple[float, float, float]:
        x = np.asarray([value], dtype=float)
        return (
            float(_trapmf(x, (0.0, 0.0, 0.25, 0.5))[0]),
            float(_trimf(x, (0.2, 0.5, 0.8))[0]),
            float(_trapmf(x, (0.5, 0.75, 1.0, 1.0))[0]),
        )

    def __call__(self, diversity: float, stagnation: float) -> float:
        if not np.isfinite(diversity) or not 0.0 <= diversity <= 1.0:
            raise ValueError("diversity must be finite and in [0, 1]")
        if not np.isfinite(stagnation) or not 0.0 <= stagnation <= 1.0:
            raise ValueError("stagnation must be finite and in [0, 1]")

        div_mu = self._input_memberships(float(diversity))
        stag_mu = self._input_memberships(float(stagnation))
        aggregated = np.zeros_like(self.universe)
        for div_idx in range(3):
            for stag_idx in range(3):
                firing = min(div_mu[div_idx], stag_mu[stag_idx])
                if firing:
                    output_idx = self.RULES[div_idx][stag_idx]
                    clipped = np.minimum(firing, self.output_memberships[output_idx])
                    aggregated = np.maximum(aggregated, clipped)

        area = float(np.sum(aggregated))
        if area == 0.0:
            return 1.0
        return float(np.sum(self.universe * aggregated) / area)


def population_diversity(positions: np.ndarray) -> float:
    """Mean pairwise absolute distance in random-key space, bounded by [0, 1]."""
    values = np.asarray(positions, dtype=float)
    if values.ndim != 2 or values.shape[0] < 2 or values.shape[1] == 0:
        raise ValueError("positions must be a 2D matrix with at least two wolves")
    if not np.all(np.isfinite(values)):
        raise ValueError("positions must be finite")
    if np.any(values < 0.0) or np.any(values > 1.0):
        raise ValueError("random keys must be in [0, 1]")
    pairwise = np.abs(values[:, None, :] - values[None, :, :])
    upper = pairwise[np.triu_indices(values.shape[0], k=1)]
    return float(np.mean(upper))
