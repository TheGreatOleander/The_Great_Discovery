
class InvariantFinder:

    def __init__(self, graph):
        self.graph = graph

    def find(self):
        invariants = []

        for node in getattr(self.graph, "nodes", []):
            props = getattr(self.graph, "properties", {}).get(node, {})
            if props:
                invariants.append({
                    "node": node,
                    "properties": props
                })

        return invariants
