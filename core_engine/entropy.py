
import math

def structural_entropy(graph):
    degrees = [graph.degree(n) for n in graph.nodes]
    total = sum(degrees)
    if total == 0:
        return 0
    entropy = 0
    for d in degrees:
        p = d / total
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy
