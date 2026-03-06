
from .base_investigator import Investigator

class CrossDomainInvestigator(Investigator):

    def investigate(self):
        proposals = []
        domains = getattr(self.graph, "domains", [])

        for d in domains:
            proposals.append({
                "type": "cross_domain_probe",
                "proposal": f"Check mapping between {d} and {self.question}"
            })

        return proposals
