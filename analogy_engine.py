
from collections import defaultdict

def build_signature(edges):

    sig = defaultdict(set)

    for a,b in edges:
        sig[a].add(b)

    return sig

def detect_analogies(edges):

    sig = build_signature(edges)

    nodes = list(sig.keys())
    results = []

    for i in range(len(nodes)):
        for j in range(i+1,len(nodes)):

            a = nodes[i]
            b = nodes[j]

            shared = sig[a].intersection(sig[b])

            if len(shared) >= 2:
                results.append((a,b))

    return results
