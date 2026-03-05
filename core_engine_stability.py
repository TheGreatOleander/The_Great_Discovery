"""
core_engine/stability.py
The Great Discovery

Stability classification wrapper. Full implementation lives in root
convergence.py. Use ConvergenceDetector there for production epoch-loop use.

This module provides a convenience classify() for one-off checks where
only instantaneous delta values are available (no history window).

Five states (matches convergence.py):
    STABLE      — compression flat, holes filling
    DEADLOCKED  — compression flat, holes static
    EXPANDING   — compression flat, holes growing (new: was folded into DEADLOCKED)
    DIVERGENT   — compression spiking
    OSCILLATORY — default / cycling
"""

from convergence import (  # noqa: F401
    STABLE,
    DEADLOCKED,
    EXPANDING,
    DIVERGENT,
    OSCILLATORY,
    EXPLORING,
    ConvergenceDetector,
)


def classify(delta_pressure, hole_delta):
    """
    Classify stability state from instantaneous delta values.

    Args:
        delta_pressure : float — ΔC(t) = C(t) - C(t-1)
        hole_delta     : float — ΔH(t) = H(t) - H(t-1), signed

    Returns:
        str : one of STABLE, DEADLOCKED, EXPANDING, DIVERGENT, OSCILLATORY
    """
    if abs(delta_pressure) > 0.15:
        return DIVERGENT
    if abs(delta_pressure) < 0.01:
        if hole_delta < -0.01:
            return STABLE
        elif abs(hole_delta) < 0.01:
            return DEADLOCKED
        else:
            return EXPANDING
    return OSCILLATORY
