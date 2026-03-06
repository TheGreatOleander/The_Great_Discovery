
from collections import defaultdict

def detect_pressure_pairs(edges):

    neighbors = defaultdict(set)

    for a,b in edges:
        neighbors[a].add(b)
        neighbors[b].add(a)

    nodes = list(neighbors.keys())
    results = []

    for i in range(len(nodes)):
        for j in range(i+1,len(nodes)):

            a = nodes[i]
            b = nodes[j]

            if (a,b) in edges or (b,a) in edges:
                continue

            shared = neighbors[a].intersection(neighbors[b])

            if len(shared) >= 2:
                results.append((a,b))

    return results
