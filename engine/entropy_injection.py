
import random

def inject_entropy(graph):

    nodes = list(graph.nodes)

    if len(nodes) < 2:
        return

    a,b = random.sample(nodes,2)

    graph.add_edge(a,b,"random_link",0.1,"entropy")
