
import time
import random

from engine.graph_store import GraphStore
from engine.hole_detector import find_holes
from engine.analogy_engine import generate_analogies
from engine.pressure_engine import apply_pressure
from engine.entropy_injection import inject_entropy
from engine.hypothesis_engine import generate_hypotheses
from engine.cycle_analyzer import detect_cycles
from engine.relations import RELATION_TYPES

MAX_ITER = 75
DISCOVERIES_PER_ITER = 5

def main():

    graph = GraphStore.load()

    print("Starting Discovery Engine v4")
    print("----------------------------")

    for i in range(MAX_ITER):

        print("iteration", i)

        holes = find_holes(graph)
        pressure = apply_pressure(graph)
        analogies = generate_analogies(graph)
        cycles = detect_cycles(graph)

        print("holes:", len(holes))
        print("pressure:", len(pressure))
        print("analogies:", len(analogies))
        print("cycles:", len(cycles))

        discoveries = 0

        for a,b in holes:

            if discoveries >= DISCOVERIES_PER_ITER:
                break

            relation = random.choice(RELATION_TYPES)
            weight = round(random.uniform(0.5,0.95),3)

            graph.add_edge(a,b,relation,weight,"hole")

            print(f"   discovered: {a} -> {b} ({relation})")

            discoveries += 1

        # generate hypotheses
        hypotheses = generate_hypotheses(graph)

        for h in hypotheses[:3]:
            print("   hypothesis:", h)

        if discoveries == 0:
            print("   injecting entropy...")
            inject_entropy(graph)

        graph.save()

        print("edges:", graph.edge_count())
        print("----------------------------")

        time.sleep(0.05)


if __name__ == "__main__":
    main()
