
import random

def inject_entropy(edges):

    nodes = set()

    for a,b in edges:
        nodes.add(a)
        nodes.add(b)

    nodes = list(nodes)

    if len(nodes) < 2:
        return

    for _ in range(3):

        a = random.choice(nodes)
        b = random.choice(nodes)

        if a != b:
            edge = (a,b)

            if edge not in edges:
                edges.append(edge)
                print("   entropy edge:", a, "->", b)
