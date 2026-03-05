"""
core_engine/convergence.py
The Great Discovery

The full convergence implementation lives at the root level: convergence.py

This module re-exports from it so that any code importing from
core_engine.convergence gets the real implementation, not a stub.

The previous version of this file was a minimal stub that lacked:
    - DEADLOCKED state
    - DIVERGENT state
    - Oscillation period detection via autocorrelation
    - Windowed derivative test
    - summary() method

All of that is in root-level convergence.py. Import from there directly,
or use this re-export.
"""

from convergence import (   # noqa: F401
    ConvergenceDetector,
    STABLE,
    DEADLOCKED,
    DIVERGENT,
    OSCILLATORY,
    EXPLORING,
)
