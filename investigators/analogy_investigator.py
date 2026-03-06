import random

class AnalogyInvestigator:

    def __init__(self):
        self.priority = 1
        self.counter = 0

    def investigate(self, region, pressure):

        if pressure < 0.8:
            return None

        self.counter += 1

        discovery_id = f"analogy_{region}_variant_{self.counter}"

        return {
            "id": discovery_id,
            "source": region,
            "type": "analogy",
            "pressure": pressure
        }