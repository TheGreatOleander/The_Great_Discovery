
import random

def seed_topology():

    nodes = [
        "mass","energy","force","field","particle","wave",
        "charge","spin","momentum","entropy","information",
        "frequency","resonance","orbit","gravity","time"
    ]

    edges = []

    for _ in range(40):

        a = random.choice(nodes)
        b = random.choice(nodes)

        if a != b:
            edges.append((a,b))

    return edges
