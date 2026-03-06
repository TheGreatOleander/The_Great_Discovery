
def apply_pressure(graph):

    pressure = []

    for e in graph.edges:
        for f in graph.edges:

            if e["b"] == f["a"]:

                pressure.append((e["a"],f["b"]))

    return pressure
