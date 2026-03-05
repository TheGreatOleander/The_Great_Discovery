
import networkx as nx

class DiscoveryGraph:
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_node(self, node_id, node_type, **attrs):
        self.graph.add_node(node_id, type=node_type, **attrs)

    def add_edge(self, source, target, relation_type, weight=1.0):
        self.graph.add_edge(source, target, relation=relation_type, weight=weight)

    def validate_cycles(self):
        return list(nx.simple_cycles(self.graph))

    def centrality(self):
        return nx.degree_centrality(self.graph)
