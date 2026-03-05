
class ConvergenceDetector:
    def __init__(self):
        self.history = []

    def record(self, pressure_value, hole_density):
        self.history.append((pressure_value, hole_density))

    def is_converging(self, window=5, threshold=0.01):
        if len(self.history) < window:
            return False
        recent = self.history[-window:]
        deltas = [
            abs(recent[i][0] - recent[i-1][0])
            for i in range(1, len(recent))
        ]
        return all(delta < threshold for delta in deltas)
