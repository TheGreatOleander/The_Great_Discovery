
import random

class DiscoveryEngine:

    def __init__(self, graph):
        self.graph = graph

    def logical_gaps(self):
        gaps = []
        for a in self.graph.nodes:
            for b,_ in self.graph.neighbors(a):
                for c,_ in self.graph.neighbors(b):
                    if c not in [n for n,_ in self.graph.neighbors(a)]:
                        gaps.append((a,c))
        return gaps

    def propose(self):
        gaps = self.logical_gaps()
        if not gaps:
            return None
        return random.choice(gaps)
