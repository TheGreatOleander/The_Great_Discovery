
class OperatorGenerator:

    def __init__(self, graph):
        self.graph = graph

    def generate(self):
        ops = []
        edges = getattr(self.graph, "edges", [])

        for a, b in edges:
            ops.append({
                "operator": f"T({a}->{b})",
                "description": f"Transformation mapping {a} to {b}"
            })

        return ops
