
class CrossDomainInvestigator:

    priority = 2

    def investigate(self, region, pressure):
        return {
            "id": f"cross_domain_{region}",
            "type": "cross_domain_pattern",
            "pressure": pressure
        }
