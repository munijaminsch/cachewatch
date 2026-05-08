"""Regression analysis: fit a polynomial to hit-ratio history."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from cachewatch.stats_tracker import StatsTracker


@dataclass
class RegressionResult:
    """Result of a polynomial regression over hit-ratio snapshots."""

    degree: int
    coefficients: List[float]  # highest-degree first
    r_squared: Optional[float]
    sample_count: int

    def __str__(self) -> str:  # pragma: no cover
        if not self.coefficients:
            return "RegressionResult(insufficient data)"
        coef_str = ", ".join(f"{c:.6f}" for c in self.coefficients)
        r2 = f"{self.r_squared:.4f}" if self.r_squared is not None else "N/A"
        return (
            f"RegressionResult(degree={self.degree}, "
            f"coefficients=[{coef_str}], r2={r2}, n={self.sample_count})"
        )


def _mean(values: List[float]) -> float:
    return sum(values) / len(values)


def _compute_r_squared(y: List[float], y_pred: List[float]) -> Optional[float]:
    if len(y) < 2:
        return None
    y_bar = _mean(y)
    ss_tot = sum((yi - y_bar) ** 2 for yi in y)
    if ss_tot == 0.0:
        return None
    ss_res = sum((yi - fi) ** 2 for yi, fi in zip(y, y_pred))
    return 1.0 - ss_res / ss_tot


def _polyfit(x: List[float], y: List[float], degree: int) -> List[float]:
    """Least-squares polynomial fit; returns coefficients highest-degree first."""
    import numpy as np  # type: ignore

    coeffs = np.polyfit(x, y, degree)
    return [float(c) for c in coeffs]


def compute_regression(
    tracker: StatsTracker,
    degree: int = 1,
) -> Optional[RegressionResult]:
    """Fit a polynomial of *degree* to the tracker's hit-ratio time series.

    Returns ``None`` when fewer than ``degree + 1`` snapshots are available.
    """
    snapshots = tracker.history()
    if len(snapshots) < degree + 1:
        return None

    try:
        import numpy as np  # noqa: F401
    except ImportError:  # pragma: no cover
        return None

    xs = [float(s.timestamp) for s in snapshots]
    ys = [s.hit_ratio for s in snapshots]

    # Normalise x to avoid numerical issues
    x0 = xs[0]
    xs_norm = [xi - x0 for xi in xs]

    coefficients = _polyfit(xs_norm, ys, degree)

    import numpy as np  # type: ignore

    poly = np.poly1d(coefficients)
    y_pred = [float(poly(xi)) for xi in xs_norm]
    r2 = _compute_r_squared(ys, y_pred)

    return RegressionResult(
        degree=degree,
        coefficients=coefficients,
        r_squared=r2,
        sample_count=len(snapshots),
    )
