
from core.graph.graph import KnowledgeGraph
from core.discovery.engine import DiscoveryEngine

def run():
    g = KnowledgeGraph()

    g.add_node("music")
    g.add_node("math")
    g.add_node("pattern")

    g.add_edge("music","pattern")
    g.add_edge("math","pattern")

    engine = DiscoveryEngine(g)

    proposal = engine.propose()
    print("Discovery proposal:", proposal)

if __name__ == "__main__":
    run()
