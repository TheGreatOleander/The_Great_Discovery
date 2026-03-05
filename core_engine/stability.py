
def classify(delta_pressure, hole_delta):
    if abs(delta_pressure) < 0.01 and hole_delta < 0:
        return "Stable"
    if hole_delta == 0 and abs(delta_pressure) < 0.01:
        return "Deadlocked"
    if abs(delta_pressure) > 1:
        return "Divergent"
    return "Oscillatory"
