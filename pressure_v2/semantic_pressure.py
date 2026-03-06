
def compute_semantic_pressure(graph):
    return len(getattr(graph, "semantic_conflicts", []))
