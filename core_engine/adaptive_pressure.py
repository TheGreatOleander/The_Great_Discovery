
def adapt_pressure(graph, pressure_dict, learning_rate=0.1):
    for node, pressure in pressure_dict.items():
        for u, v, data in graph.in_edges(node, data=True):
            if data.get("relation") == "restricts":
                data["weight"] = max(0, data.get("weight", 1) - learning_rate * pressure)
            elif data.get("relation") == "enables":
                data["weight"] = data.get("weight", 1) + learning_rate * pressure
    return graph
