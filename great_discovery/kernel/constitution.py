
class Constitution:
    def __init__(self,
                 min_invariant_score=0.75,
                 max_entropy=5.0,
                 max_pressure=10.0,
                 max_mutation_delta=0.2):

        self.min_invariant_score = min_invariant_score
        self.max_entropy = max_entropy
        self.max_pressure = max_pressure
        self.max_mutation_delta = max_mutation_delta

    def validate(self, state, mutation_delta=0.0):
        if state.entropy > self.max_entropy:
            return False

        if state.pressure > self.max_pressure:
            return False

        if mutation_delta > self.max_mutation_delta:
            return False

        return True
