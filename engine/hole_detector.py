
def find_holes(graph):

    holes = []
    nodes = list(graph.nodes)

    for a in nodes:
        for b in nodes:

            if a == b:
                continue

            exists = any(e["a"]==a and e["b"]==b for e in graph.edges)

            if not exists:
                holes.append((a,b))

    return holes[:200]
