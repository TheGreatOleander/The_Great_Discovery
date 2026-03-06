
from .analogy_investigator import AnalogyInvestigator
from .cross_domain_investigator import CrossDomainInvestigator

class InvestigationManager:

    def __init__(self, graph):
        self.graph = graph

    def run(self, question):
        investigators = [
            AnalogyInvestigator(self.graph, question),
            CrossDomainInvestigator(self.graph, question)
        ]

        candidates = []

        for inv in investigators:
            candidates.extend(inv.investigate())

        return candidates
