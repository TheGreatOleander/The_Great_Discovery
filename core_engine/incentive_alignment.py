
def incentive_misalignment(graph):
    misalignment = {}
    for node in graph.nodes:
        incentives = [
            d.get("weight", 1)
            for _, _, d in graph.out_edges(node, data=True)
            if d.get("relation") == "incentivizes"
        ]
        constraints = [
            d.get("weight", 1)
            for _, _, d in graph.out_edges(node, data=True)
            if d.get("relation") == "restricts"
        ]
        misalignment[node] = sum(incentives) - sum(constraints)
    return misalignment
