
class KnowledgeTopology:

    def __init__(self):
        self.nodes = {}
        self.edges = {}

    def add_node(self, node):
        self.nodes[node] = {"pressure":0}

    def add_edge(self, a, b):
        self.edges.setdefault(a, []).append(b)
        self.edges.setdefault(b, []).append(a)

    def detect_instability(self):
        unstable = []
        for n,data in self.nodes.items():
            if data["pressure"] > 0.8:
                unstable.append(n)
        return unstable

    def integrate(self, discovery):
        node = discovery["id"]
        self.add_node(node)
