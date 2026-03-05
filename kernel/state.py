
import copy

class EngineState:
    def __init__(self, graph, governance, invariants, seed=42):
        self.graph = graph
        self.governance = governance
        self.invariants = invariants

        self.pressure = 0.0
        self.entropy = 0.0
        self.holes = []

        self.step_count = 0
        self.history = []
        self.seed = seed

    def snapshot(self):
        return {
            "step": self.step_count,
            "pressure": self.pressure,
            "entropy": self.entropy,
            "holes": len(self.holes),
            "governance": copy.deepcopy(self.governance),
        }
