
def mutate_governance(graph, governance_nodes, threshold=0.5):
    for node in governance_nodes:
        influence = graph.degree(node)
        if influence < threshold:
            graph.nodes[node]["status"] = "weakened"
        else:
            graph.nodes[node]["status"] = "dominant"
    return graph
