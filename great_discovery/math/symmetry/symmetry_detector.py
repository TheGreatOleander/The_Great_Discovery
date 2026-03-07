
class SymmetryDetector:
    """Detects structural symmetries in the knowledge graph."""

    def __init__(self, graph):
        self.graph = graph

    def detect(self):
        symmetries = []
        nodes = getattr(self.graph, "nodes", [])

        for a in nodes:
            for b in nodes:
                if a == b:
                    continue
                if getattr(self.graph, "degree", lambda x: 0)(a) == getattr(self.graph, "degree", lambda x: 0)(b):
                    symmetries.append((a, b))

        return symmetries
