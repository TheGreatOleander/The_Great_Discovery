
import random
from topology_seed import seed_topology
from hole_detector import find_nameable_holes
from topology_pressure import detect_pressure_pairs
from analogy_engine import detect_analogies
from entropy_injection import inject_entropy
from graph_store import save_graph, load_graph

MAX_INSERT = 5

def apply_discoveries(edges, proposals):

    added = 0

    for src, dst, reason in proposals:

        if added >= MAX_INSERT:
            break

        edge = (src, dst)

        if edge not in edges:

            edges.append(edge)
            added += 1

            print(f"   discovered: {src} -> {dst}  ({reason})")

    return added


def run():

    print("Starting Discovery Engine v+2")

    edges = load_graph()

    if not edges:
        edges = seed_topology()

    for iteration in range(25):

        print("----------------")
        print("iteration", iteration)

        holes = find_nameable_holes(edges)
        pressure = detect_pressure_pairs(edges)
        analogies = detect_analogies(edges)

        print("holes:", len(holes))
        print("pressure:", len(pressure))
        print("analogies:", len(analogies))

        proposals = []

        for h in holes[:10]:
            proposals.append((h["src"], h["dst"], "hole"))

        for a,b in pressure[:10]:
            proposals.append((a,b,"pressure"))

        for a,b in analogies[:10]:
            proposals.append((a,b,"analogy"))

        added = apply_discoveries(edges, proposals)

        if added == 0:
            print("   injecting entropy...")
            inject_entropy(edges)

        save_graph(edges)

        print("edges total:", len(edges))


if __name__ == "__main__":
    run()
