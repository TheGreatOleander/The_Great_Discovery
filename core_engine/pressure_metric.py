
def calculate_pressure(graph):
    pressures = {}
    for node in graph.nodes:
        incoming = graph.in_edges(node, data=True)
        restrictive = sum(1 for _, _, d in incoming if d.get("relation") == "restricts")
        enabling = sum(1 for _, _, d in incoming if d.get("relation") == "enables")
        pressures[node] = restrictive - enabling
    return pressures
