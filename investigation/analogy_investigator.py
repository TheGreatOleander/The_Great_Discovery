
from .base_investigator import Investigator

class AnalogyInvestigator(Investigator):

    def investigate(self):
        results = []
        similar = getattr(self.graph, "find_similar", lambda x: [])(self.question)

        for node in similar:
            results.append({
                "type": "analogy_hypothesis",
                "source": node,
                "proposal": f"Concept similar to {node} may resolve {self.question}"
            })

        return results
