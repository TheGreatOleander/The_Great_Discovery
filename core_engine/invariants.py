
class InvariantEngine:
    def __init__(self, graph):
        self.graph = graph

    def check_orphan_nodes(self):
        return [n for n in self.graph.nodes if self.graph.degree(n) == 0]

    def check(self):
        issues = {}
        orphans = self.check_orphan_nodes()
        if orphans:
            issues["orphans"] = orphans
        return issues
