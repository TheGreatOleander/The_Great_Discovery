import random
from hole_detector import find_nameable_holes
from topology_pressure import detect_pressure_pairs
from analogy_engine import detect_analogies


MAX_INSERT = 20
ITERATIONS = 200


def inject_entropy(edges):

    nodes = set()

    for src, dst in edges:
        nodes.add(src)
        nodes.add(dst)

    nodes = list(nodes)

    if len(nodes) < 2:
        return

    a = random.choice(nodes)
    b = random.choice(nodes)

    if a != b:
        edges.add((a, b))


def extract_edge(item):
    """
    Converts detector outputs into (src,dst) tuples
    """

    if isinstance(item, tuple):
        return item

    if isinstance(item, dict):

        if "src" in item and "dst" in item:
            return (item["src"], item["dst"])

        if "a" in item and "b" in item:
            return (item["a"], item["b"])

    return None


def run_discovery(edges):

    print("Starting Discovery Engine v+2")

    for iteration in range(ITERATIONS):

        print("----------------")
        print("iteration", iteration)

        holes = find_nameable_holes(edges)
        pressure = detect_pressure_pairs(edges)
        analogies = detect_analogies(edges)

        print("holes:", len(holes))
        print("pressure:", len(pressure))
        print("analogies:", len(analogies))

        proposals = []

        proposals.extend(holes[:20])
        proposals.extend(pressure[:20])
        proposals.extend(analogies[:50])

        # convert to edges
        edges_to_try = []

        for item in proposals:

            edge = extract_edge(item)

            if edge:
                edges_to_try.append(edge)

        # deduplicate edges
        edges_to_try = list(set(edges_to_try))

        random.shuffle(edges_to_try)

        added = 0

        for src, dst in edges_to_try:

            if (src, dst) not in edges:

                edges.add((src, dst))
                added += 1

                print(f"   discovered: {src} -> {dst}")

            if added >= MAX_INSERT:
                break

        if added == 0:

            print("   injecting entropy...")
            inject_entropy(edges)

        print("edges total:", len(edges))


def load_graph():

    edges = set()

    nodes = [
        "A","B","C","D","E","F","G","H",
        "I","J","K","L","M","N","O","P"
    ]

    for i in range(len(nodes)):
        for j in range(len(nodes)):

            if i != j and random.random() < 0.1:
                edges.add((nodes[i], nodes[j]))

    return edges


if __name__ == "__main__":

    edges = load_graph()

    run_discovery(edges)