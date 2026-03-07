
from copy import deepcopy
import random

class GreatDiscoveryEngine:
    def __init__(self, state, constitution,
                 hole_detector,
                 pressure_metric,
                 entropy_metric,
                 governance_mutator):

        self.state = state
        self.constitution = constitution

        self.hole_detector = hole_detector
        self.pressure_metric = pressure_metric
        self.entropy_metric = entropy_metric
        self.governance_mutator = governance_mutator

        random.seed(self.state.seed)

    def compute_mutation_delta(self, before, after):
        if isinstance(before, dict) and isinstance(after, dict):
            delta = 0.0
            for k in before:
                if k in after and isinstance(before[k], (int, float)):
                    delta += abs(before[k] - after[k])
            return delta
        return 0.0

    def step(self):
        original_state = deepcopy(self.state)
        governance_before = deepcopy(self.state.governance)

        self.state.holes = self.hole_detector(self.state)
        self.state.pressure = self.pressure_metric(self.state)
        self.governance_mutator(self.state)

        mutation_delta = self.compute_mutation_delta(
            governance_before,
            self.state.governance
        )

        self.state.entropy = self.entropy_metric(self.state)

        if not self.constitution.validate(self.state, mutation_delta):
            self.state = original_state
            return False

        self.state.step_count += 1
        self.state.history.append(self.state.snapshot())

        return True
