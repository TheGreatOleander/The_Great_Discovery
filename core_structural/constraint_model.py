
class ConstraintModel:
    def __init__(self):
        self.constraints = []

    def add_constraint(self, func, weight=1.0):
        self.constraints.append((func, weight))

    def pressure(self, state):
        total = 0.0
        for func, weight in self.constraints:
            violation = abs(func(state))
            total += weight * violation
        return total
