class KnowledgeTopology:

    def __init__(self):
        self.nodes = {}
        self.edges = {}

    def add_node(self, node):
        if node not in self.nodes:
            self.nodes[node] = {"pressure": 0}

    def add_edge(self, a, b):
        self.edges.setdefault(a, []).append(b)
        self.edges.setdefault(b, []).append(a)

    # FIX: read pressure from PressureField instead of stale node values
    def detect_instability(self, pressure_field):
        unstable = []

        for n in self.nodes:
            pressure = pressure_field.measure(n)

            if pressure > 0.8:
                unstable.append(n)

        return unstable

    def integrate(self, discovery):
        node = discovery["id"]
        self.add_node(node)