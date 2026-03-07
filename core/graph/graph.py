
class KnowledgeGraph:

    def __init__(self):
        self.nodes = set()
        self.edges = {}

    def add_node(self, node):
        self.nodes.add(node)

    def add_edge(self, a, b, relation="related"):
        self.edges.setdefault(a, []).append((b, relation))

    def neighbors(self, node):
        return self.edges.get(node, [])
