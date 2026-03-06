
def compute_cross_domain_pressure(graph):
    return len(getattr(graph, "domain_bridges", []))
