"""
convergence.py — Phase 4 (hardened)
The Great Discovery

═══════════════════════════════════════════════════════════════════════════════
STABILITY CLASSIFICATION — FIVE STATES
═══════════════════════════════════════════════════════════════════════════════

Previous implementation had four states. DEADLOCKED fired on two structurally
distinct conditions that warrant different engine responses:

    OLD DEADLOCKED: mean_ΔC < ε  AND  mean_ΔH ≥ -ε
    This caught both:
        (a) mean_ΔH ≈ 0  — holes static, compression flat  → true deadlock
        (b) mean_ΔH > 0  — holes growing, compression flat → structural expansion

    These are different. A deadlocked engine is frozen. An expanding engine
    is generating new structural demands faster than it fills them — topology
    is stable but still hungry. The response should differ:

        DEADLOCKED  → perturbation (inject noise, raise temperature)
        EXPANDING   → slow settling throttle (let holes accumulate, sharpen)

FIVE STATES:

    STABLE      : mean_ΔC < ε   AND  mean_ΔH < -ε
                  Pressure stabilizing, holes filling. Healthy convergence.

    DEADLOCKED  : mean_ΔC < ε   AND  |mean_ΔH| < ε
                  Compression flat, holes static. Structure frozen.
                  Response: perturbation + temperature raise.

    EXPANDING   : mean_ΔC < ε   AND  mean_ΔH > ε
                  Compression flat, holes growing. Topology stable but hungry.
                  New structural demands emerging faster than they're filled.
                  Response: reduce settling throttle, let holes sharpen.

    DIVERGENT   : |ΔC(t)| > divergence_threshold
                  Pressure increasing. Topology destabilizing.
                  Response: raise exploration temperature.

    OSCILLATORY : none of the above
                  Pressure cycling without clear direction.

    EXPLORING   : fewer than window epochs recorded.

─────────────────────────────────────────────────────────────────────────────
CONVERGENCE DETECTION — WINDOWED DERIVATIVE TEST
─────────────────────────────────────────────────────────────────────────────

    mean_ΔC = (1/W) Σ |C(t) - C(t-1)|  over last W epochs
    mean_ΔH = (1/W) Σ  H(t) - H(t-1)   over last W epochs  (signed)

    CONVERGING if:  mean_ΔC < ε  (ε = convergence_threshold, default 0.01)

─────────────────────────────────────────────────────────────────────────────
OSCILLATION PERIOD DETECTION
─────────────────────────────────────────────────────────────────────────────

    R(k) = [Σ_t ΔC(t)·ΔC(t-k)] / [Σ_t ΔC(t)²]

    Oscillation detected if R(k) > autocorr_threshold for k ∈ [2, W//2].
    Returns smallest such k as the oscillation period.

═══════════════════════════════════════════════════════════════════════════════
"""

import math
from collections import deque


# Stability states
STABLE      = "Stable"
DEADLOCKED  = "Deadlocked"
EXPANDING   = "Expanding"
DIVERGENT   = "Divergent"
OSCILLATORY = "Oscillatory"
EXPLORING   = "Exploring"


class ConvergenceDetector:
    """
    Tracks compression and hole density across epochs and classifies
    the engine's current stability state.

    Usage in driver loop:
        detector = ConvergenceDetector()
        state = detector.record(compression, hole_density)
        if state == STABLE:
            ...
        elif state == DEADLOCKED:
            # inject perturbation
        elif state == EXPANDING:
            # reduce settling throttle, let holes sharpen
        elif state == DIVERGENT:
            # raise exploration temperature
    """

    def __init__(self,
                 window=8,
                 convergence_threshold=0.01,
                 divergence_threshold=0.15,
                 autocorr_threshold=0.6):
        """
        Args:
            window                : int   — rolling window size W
            convergence_threshold : float — ε for mean_ΔC and mean_ΔH tests
            divergence_threshold  : float — |ΔC| threshold for DIVERGENT
            autocorr_threshold    : float — R(k) threshold for oscillation
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
            hole_density : float — H(t) = unfilled_holes / total_holes

        Returns:
            str : one of STABLE, DEADLOCKED, EXPANDING, DIVERGENT,
                  OSCILLATORY, EXPLORING
        """
        self._compression_history.append(compression)
        self._hole_density_history.append(hole_density)

        state = self._classify()
        self._state_history.append(state)
        return state

    def is_converging(self):
        """True if current state is STABLE."""
        if not self._state_history:
            return False
        return self._state_history[-1] == STABLE

    def summary(self):
        """Return current convergence diagnostics dict."""
        if len(self._compression_history) < 2:
            return {
                'state': EXPLORING,
                'mean_delta_c': None,
                'mean_delta_h': None,
                'oscillation_period': None,
                'epochs_tracked': len(self._compression_history),
            }

        c_deltas = self._compression_deltas()
        h_deltas = self._hole_density_deltas()
        mean_dc  = sum(abs(d) for d in c_deltas) / len(c_deltas) if c_deltas else 0.0
        mean_dh  = (sum(h_deltas[-self.window:]) / self.window
                    if len(h_deltas) >= self.window else 0.0)
        period   = self._detect_oscillation_period(c_deltas)
        state    = self._classify()

        return {
            'state':              state,
            'mean_delta_c':       round(mean_dc, 6),
            'mean_delta_h':       round(mean_dh, 6),
            'oscillation_period': period,
            'epochs_tracked':     len(self._compression_history),
        }

    # ── Internal classification ───────────────────────────────────────────────

    def _compression_deltas(self):
        h = list(self._compression_history)
        return [h[i] - h[i-1] for i in range(1, len(h))]

    def _hole_density_deltas(self):
        h = list(self._hole_density_history)
        return [h[i] - h[i-1] for i in range(1, len(h))]

    def _mean_abs_delta(self, deltas, tail=None):
        if not deltas:
            return math.inf
        window_deltas = deltas[-tail:] if tail else deltas
        return sum(abs(d) for d in window_deltas) / len(window_deltas)

    def _detect_oscillation_period(self, deltas):
        """
        Detect oscillation period via normalized autocorrelation of ΔC.

            R(k) = [Σ_t ΔC(t)·ΔC(t-k)] / [Σ_t ΔC(t)²]

        Returns smallest lag k ∈ [2, W//2] where R(k) > autocorr_threshold,
        or None if no periodic component detected.
        """
        if len(deltas) < self.window * 2:
            return None

        mean_d   = sum(deltas) / len(deltas)
        d        = [x - mean_d for x in deltas]
        variance = sum(x * x for x in d)
        if variance < 1e-12:
            return None

        max_lag = max(2, len(d) // 2)
        for k in range(2, max_lag + 1):
            autocorr = sum(d[i] * d[i - k] for i in range(k, len(d)))
            if autocorr / variance > self.autocorr_threshold:
                return k

        return None

    def _classify(self):
        """
        Classify current stability state.

        Priority order:
            1. EXPLORING  — insufficient history
            2. DIVERGENT  — last ΔC exceeds divergence threshold
            3. STABLE     — mean_ΔC < ε  AND  mean_ΔH < -ε  (filling)
            4. DEADLOCKED — mean_ΔC < ε  AND  |mean_ΔH| < ε  (frozen)
            5. EXPANDING  — mean_ΔC < ε  AND  mean_ΔH > ε   (hungry)
            6. OSCILLATORY — default
        """
        if len(self._compression_history) < self.window:
            return EXPLORING

        c_deltas = self._compression_deltas()
        h_deltas = self._hole_density_deltas()

        last_dc = abs(c_deltas[-1]) if c_deltas else 0.0
        if last_dc > self.divergence_threshold:
            return DIVERGENT

        mean_dc = self._mean_abs_delta(c_deltas, tail=self.window)
        mean_dh = (sum(h_deltas[-self.window:]) / self.window
                   if len(h_deltas) >= self.window else 0.0)

        ε = self.convergence_threshold

        if mean_dc < ε:
            if mean_dh < -ε:
                return STABLE       # holes filling, pressure stable
            elif abs(mean_dh) < ε:
                return DEADLOCKED   # holes static, pressure static → frozen
            else:
                return EXPANDING    # holes growing, pressure stable → hungry

        return OSCILLATORY
