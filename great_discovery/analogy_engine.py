"""
analogy_engine.py
The Great Discovery

Detects analogical connections using three structural patterns.
Previously used only Pattern 1, which exhausted at iteration 21 and
caused the permanent stall seen in output.txt.

PATTERN 1 -- Shared target
    A->C and B->C (same target), A->X but not B->X:
    suggest B->X  ("what works for A probably works for B")

PATTERN 2 -- Sibling bridge (co-citation)
    P->A and P->B (same parent), A->X but not B->X:
    suggest B->X  ("siblings of the same node share connections")

PATTERN 3 -- Symmetry
    A->B exists but B->A does not:
    suggest B->A  ("many relations are bidirectional")
"""


def detect_analogies(edges):
    """
    Find candidate new edges via structural analogy.

    Args:
        edges: list of (src, dst) tuples

    Returns:
        list of (src, dst) tuples -- suggested new edges, deduplicated,
        with existing edges removed
    """
    edge_set = set(edges)
    results  = set()

    # Build adjacency
    outgoing = {}
    for src, dst in edges:
        outgoing.setdefault(src, set()).add(dst)

    nodes = list(outgoing.keys())

    # -- Pattern 1: Shared target --
    # For each pair (a, b) that both point to some common node c:
    # if a->x but not b->x, suggest b->x (and vice versa)
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            a, b   = nodes[i], nodes[j]
            a_out  = outgoing.get(a, set())
            b_out  = outgoing.get(b, set())
            shared = a_out & b_out
            if not shared:
                continue
            for x in a_out - b_out:
                results.add((b, x))
            for x in b_out - a_out:
                results.add((a, x))

    # -- Pattern 2: Sibling bridge --
    # For each parent p with children {a, b, ...}:
    # if a->x but not b->x, suggest b->x
    for parent in nodes:
        children = list(outgoing.get(parent, set()))
        for i in range(len(children)):
            for j in range(i + 1, len(children)):
                a, b  = children[i], children[j]
                a_out = outgoing.get(a, set())
                b_out = outgoing.get(b, set())
                for x in a_out - b_out:
                    if x != b:
                        results.add((b, x))
                for x in b_out - a_out:
                    if x != a:
                        results.add((a, x))

    # -- Pattern 3: Symmetry --
    # If a->b but not b->a, suggest b->a
    for src, dst in edges:
        if (dst, src) not in edge_set:
            results.add((dst, src))

    # Remove edges that already exist
    results -= edge_set

    return list(results)
