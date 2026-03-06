
def compute_topology_pressure(graph):
    return len(getattr(graph, "holes", []))
