
import networkx as nx

class GraphModel:
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_actor(self, actor):
        self.graph.add_node(actor)

    def add_relation(self, source, target, weight=1.0):
        self.graph.add_edge(source, target, weight=weight)

    def fragility_index(self):
        if len(self.graph) == 0:
            return 0.0
        centrality = nx.betweenness_centrality(self.graph, weight="weight")
        total = sum(centrality.values())
        if total == 0:
            return 0.0
        return max(centrality.values()) / total
