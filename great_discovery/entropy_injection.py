"""
entropy_injection.py
The Great Discovery

Hole-aware entropy injection. Previously added 3 random edges per call with
no awareness of where the structural voids actually were -- ran 189 consecutive
times in output.txt with zero effect on the stall.

New strategy: 2 targeted injections aimed at known holes + 1 random.
This means entropy is spent where the structure is actually asking for it.

inject_entropy(edges, holes=None)
    edges : list of (src, dst) tuples -- mutated in place
    holes : optional list of hole dicts from hole_detector (src/dst keys)
            Can use either 'src'/'dst' (old integer format) or
            'src_id'/'dst_id' (new SQLite profile format)
"""

import random


def inject_entropy(edges, holes=None):
    """
    Inject new edges to break stagnation.

    If holes are provided, 2 of the 3 injections target high-precision holes
    directly. The third is random to maintain exploration diversity.

    Args:
        edges : list of (src, dst) tuples, mutated in place
        holes : optional list of hole dicts from find_nameable_holes()
    """
    nodes = list({n for e in edges for n in e})
    if len(nodes) < 2:
        return

    edge_set   = set(edges)
    injections = []

    # Targeted: aim at the top holes we already know about
    if holes:
        for hole in holes[:2]:
            # Support both old format (src/dst) and new profile format (src_id/dst_id)
            src = hole.get("src_id", hole.get("src"))
            dst = hole.get("dst_id", hole.get("dst"))
            if src is not None and dst is not None:
                edge = (src, dst)
                if edge not in edge_set and src != dst:
                    injections.append(edge)

    # Random: fill remaining slots up to 3 total
    attempts = 0
    while len(injections) < 3 and attempts < 20:
        a = random.choice(nodes)
        b = random.choice(nodes)
        if a != b and (a, b) not in edge_set:
            injections.append((a, b))
        attempts += 1

    for edge in injections:
        if edge not in edge_set:
            edges.append(edge)
            edge_set.add(edge)
            print(f"   entropy edge: {edge[0]} -> {edge[1]}")
