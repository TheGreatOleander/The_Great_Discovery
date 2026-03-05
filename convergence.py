"""
convergence.py — Phase 3 (hardened)
The Great Discovery

═══════════════════════════════════════════════════════════════════════════════
MATHEMATICS — CONVERGENCE DETECTION
═══════════════════════════════════════════════════════════════════════════════

PREVIOUS IMPLEMENTATION:
    Checked whether all |ΔC| in a window were below a threshold.
    Problem 1: only tracked pressure, not hole density — incomplete signal.
    Problem 2: not wired into the driver loop — never called.
    Problem 3: no distinction between convergence types (stable vs deadlocked
               vs oscillatory vs divergent).

THIS IMPLEMENTATION:
    Full stability classification using both signals and their derivatives,
    consistent with the HARDENING_SPEC definitions.

─────────────────────────────────────────────────────────────────────────────
1. SIGNALS TRACKED
─────────────────────────────────────────────────────────────────────────────
    C(t)  — compression ratio at epoch t             (primary pressure signal)
    H(t)  — hole density at epoch t = unfilled/expected
    ΔC(t) = C(t) - C(t-1)                           (first derivative of C)
    ΔH(t) = H(t) - H(t-1)                           (first derivative of H)

─────────────────────────────────────────────────────────────────────────────
2. STABILITY CLASSIFICATION (from HARDENING_SPEC)
─────────────────────────────────────────────────────────────────────────────
    STABLE      : |ΔC| → 0   AND   ΔH < 0
                  Pressure stabilizing, holes filling. Healthy convergence.

    DEADLOCKED  : |ΔC| → 0   AND   ΔH ≈ 0
                  Pressure flat, holes neither filling nor growing.
                  Structure is frozen — not converging, not exploring.

    DIVERGENT   : |ΔC| >> threshold
                  Pressure magnitude increasing — topology destabilizing.

    OSCILLATORY : none of the above
                  Pressure cycling without clear direction.

─────────────────────────────────────────────────────────────────────────────
3. CONVERGENCE DETECTION — WINDOWED DERIVATIVE TEST
─────────────────────────────────────────────────────────────────────────────
    We use a rolling window of W epochs to estimate the derivative of C.

    Finite difference approximation of dC/dt over window [t-W, t]:

        dC/dt ≈ (C(t) - C(t-W)) / W        (forward difference)

    Alternatively, the mean of first differences in the window:

        mean_ΔC = (1/(W-1)) Σ_{i=t-W+1}^{t} |C(i) - C(i-1)|

    We use mean_ΔC for robustness (less sensitive to single-epoch spikes).

    CONVERGING if:  mean_ΔC < ε   (ε = convergence_threshold)

─────────────────────────────────────────────────────────────────────────────
4. MULTI-CYCLE DETECTION
─────────────────────────────────────────────────────────────────────────────
    Oscillation period detection via autocorrelation of ΔC series:

    For lag k:
        R(k) = Σ_{t} ΔC(t) · ΔC(t-k)   /   Σ_{t} ΔC(t)²

    If R(k) > autocorr_threshold for some k ∈ [2, W//2], the signal has
    a periodic component with period k. This is reported as OSCILLATORY
    with the detected period.

    Practical threshold: R(k) > 0.6 indicates meaningful periodicity.

═══════════════════════════════════════════════════════════════════════════════
"""

import math
from collections import deque


# Stability states (matches HARDENING_SPEC classifications)
STABLE      = "Stable"
DEADLOCKED  = "Deadlocked"
DIVERGENT   = "Divergent"
OSCILLATORY = "Oscillatory"
EXPLORING   = "Exploring"   # not enough data yet


class ConvergenceDetector:
    """
    Tracks compression and hole density across epochs and classifies
    the engine's current stability state.

    Usage in driver loop:
        detector = ConvergenceDetector()
        ...
        state = detector.record(compression, hole_density)
        if state == STABLE:
            # engine has converged
        elif state == DIVERGENT:
            # lower governance threshold, increase exploration bias
    """

    def __init__(self,
                 window=8,
                 convergence_threshold=0.01,
                 divergence_threshold=0.15,
                 autocorr_threshold=0.6):
        """
        Args:
            window                : int   — rolling window size W for derivative estimation
            convergence_threshold : float — ε for mean_ΔC convergence test
            divergence_threshold  : float — |ΔC| threshold for DIVERGENT classification
            autocorr_threshold    : float — R(k) threshold for oscillation detection
        """
        self.window                = window
        self.convergence_threshold = convergence_threshold
        self.divergence_threshold  = divergence_threshold
        self.autocorr_threshold    = autocorr_threshold

        self._compression_history  = deque(maxlen=window * 2)
        self._hole_density_history = deque(maxlen=window * 2)
        self._state_history        = deque(maxlen=window * 2)

    # ── Public interface ──────────────────────────────────────────────────────

    def record(self, compression, hole_density):
        """
        Record one epoch's measurements and return current stability state.

        Args:
            compression  : float — C(t) from pressure_snapshot()
            hole_density : float — H(t) = unfilled_holes / expected_holes
                                   Pass 0.0 if hole count unavailable.

        Returns:
            str : one of STABLE, DEADLOCKED, DIVERGENT, OSCILLATORY, EXPLORING
        """
        self._compression_history.append(compression)
        self._hole_density_history.append(hole_density)

        state = self._classify()
        self._state_history.append(state)
        return state

    def is_converging(self):
        """
        Returns True if the engine is in a STABLE convergence state.
        Convenience method for simple boolean checks in the driver.
        """
        if len(self._state_history) == 0:
            return False
        return self._state_history[-1] == STABLE

    def summary(self):
        """
        Return a dict of current convergence diagnostics for driver reporting.
        """
        if len(self._compression_history) < 2:
            return {'state': EXPLORING, 'mean_delta_c': None,
                    'oscillation_period': None, 'epochs_tracked': len(self._compression_history)}

        deltas   = self._compression_deltas()
        mean_dc  = sum(abs(d) for d in deltas) / len(deltas) if deltas else 0.0
        period   = self._detect_oscillation_period(deltas)
        state    = self._classify()

        return {
            'state':              state,
            'mean_delta_c':       round(mean_dc, 6),
            'oscillation_period': period,
            'epochs_tracked':     len(self._compression_history),
        }

    # ── Internal classification ───────────────────────────────────────────────

    def _compression_deltas(self):
        """First differences of compression history: ΔC(t) = C(t) - C(t-1)."""
        h = list(self._compression_history)
        return [h[i] - h[i-1] for i in range(1, len(h))]

    def _hole_density_deltas(self):
        """First differences of hole density history."""
        h = list(self._hole_density_history)
        return [h[i] - h[i-1] for i in range(1, len(h))]

    def _mean_abs_delta(self, deltas, tail=None):
        """
        Mean absolute first difference over a window tail.

        Estimates  mean_ΔC = (1/W) Σ |ΔC(t)|  over the last `tail` values.
        This is the primary convergence criterion: mean_ΔC < ε → converging.
        """
        if not deltas:
            return math.inf
        window_deltas = deltas[-tail:] if tail else deltas
        return sum(abs(d) for d in window_deltas) / len(window_deltas)

    def _detect_oscillation_period(self, deltas):
        """
        Detect oscillation period via normalized autocorrelation.

            R(k) = [Σ_t ΔC(t)·ΔC(t-k)] / [Σ_t ΔC(t)²]

        Returns the smallest lag k ∈ [2, W//2] where R(k) > autocorr_threshold,
        or None if no periodic component is detected.

        Requires at least 2*window deltas for reliable estimation.
        """
        if len(deltas) < self.window * 2:
            return None

        # Zero-mean the series (oscillation detection works on deviations)
        mean_d = sum(deltas) / len(deltas)
        d      = [x - mean_d for x in deltas]

        variance = sum(x * x for x in d)
        if variance < 1e-12:
            return None

        max_lag = max(2, len(d) // 2)
        for k in range(2, max_lag + 1):
            autocorr = sum(d[i] * d[i - k] for i in range(k, len(d)))
            r        = autocorr / variance
            if r > self.autocorr_threshold:
                return k

        return None

    def _classify(self):
        """
        Classify current stability state using compression and hole density signals.

        Classification rules (in priority order):

        1. EXPLORING : fewer than `window` epochs recorded — insufficient data
        2. DIVERGENT : |ΔC| in most recent epoch exceeds divergence_threshold
        3. STABLE    : mean_ΔC < ε  AND  mean hole density delta < 0
                       (pressure stabilizing AND holes filling)
        4. DEADLOCKED: mean_ΔC < ε  AND  mean hole density delta ≈ 0
                       (pressure flat AND holes not filling)
        5. OSCILLATORY: default — pressure cycling without clear direction
        """
        if len(self._compression_history) < self.window:
            return EXPLORING

        c_deltas = self._compression_deltas()
        h_deltas = self._hole_density_deltas()

        # Most recent delta — check for divergence first
        last_dc = abs(c_deltas[-1]) if c_deltas else 0.0
        if last_dc > self.divergence_threshold:
            return DIVERGENT

        # Mean absolute delta over window
        mean_dc = self._mean_abs_delta(c_deltas, tail=self.window)

        # Mean hole density change over window
        mean_dh = (sum(h_deltas[-self.window:]) / self.window
                   if len(h_deltas) >= self.window else 0.0)

        if mean_dc < self.convergence_threshold:
            if mean_dh < -1e-6:
                return STABLE       # Holes filling, pressure stable
            else:
                return DEADLOCKED   # Holes static, pressure static

        return OSCILLATORY
