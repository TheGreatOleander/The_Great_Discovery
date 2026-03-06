
class TheoremInvestigator:

    priority = 2

    def investigate(self, region, pressure):

        if pressure < 1:
            return None

        return {
            "id": f"theorem_{region}",
            "source": region,
            "type": "theorem_candidate",
            "pressure": pressure
        }
