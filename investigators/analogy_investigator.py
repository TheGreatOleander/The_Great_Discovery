
class AnalogyInvestigator:

    priority = 1

    def investigate(self, region, pressure):

        if pressure < 0.5:
            return None

        return {
            "id": f"analogy_{region}",
            "source": region,
            "type": "analogy",
            "pressure": pressure
        }
