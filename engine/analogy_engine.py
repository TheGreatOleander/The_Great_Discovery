
def generate_analogies(graph):

    analogies = []

    for e in graph.edges:

        analogies.append((e["b"],e["a"]))

    return analogies
