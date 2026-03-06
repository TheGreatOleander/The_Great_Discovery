
class DomainExplorer:

    def __init__(self, domains):
        self.domains = domains

    def expand(self, hypothesis):

        results = {}

        for d in self.domains:
            results[d] = f"{hypothesis} applied to {d}"

        return results
