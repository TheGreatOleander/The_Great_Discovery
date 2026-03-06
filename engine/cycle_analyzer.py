
def detect_cycles(graph):

    cycles = []

    for e in graph.edges:
        for f in graph.edges:

            if e["a"] == f["b"] and e["b"] == f["a"]:

                cycles.append((e,f))

    return cycles
