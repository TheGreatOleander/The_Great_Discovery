"""
hole_detector.py
The Great Discovery

Three hole types are detected:

1. TRANSITIVE  — a->b, b->c, missing a->c  (original)
2. CO-CITATION — c->a and c->b, missing a->b  (shared parent implies sibling connection)
3. SYMMETRY    — a->b exists, missing b->a  (relation may be bidirectional)

Holes are ranked by precision (how many surrounding constraints shape the gap)
and returned as rich profiles that questioner.py can compose questions from.

find_nameable_holes(conn, limit) -- SQLite-aware, used by driver.py
analyze_hole(conn, src_id, dst_id) -- builds a single profile for a known pair
"""

from collections import Counter


def _build_profile(conn, src_id, dst_id, hole_type):
    """
    Build the full hole profile dict that questioner.compose_question() expects.
    Queries the SQLite graph to gather structural context around the gap.
    """
    c = conn.cursor()

    c.execute("SELECT concept, domain FROM nodes WHERE id=?", (src_id,))
    src_row = c.fetchone()
    c.execute("SELECT concept, domain FROM nodes WHERE id=?", (dst_id,))
    dst_row = c.fetchone()

    if not src_row or not dst_row:
        return None

    src_concept, src_domain = src_row
    dst_concept, dst_domain = dst_row

    c.execute("SELECT relation_type FROM edges WHERE dst=?", (src_id,))
    inbound_rels = [r[0] for r in c.fetchall()]

    c.execute("SELECT relation_type FROM edges WHERE src=?", (src_id,))
    outbound_rels = [r[0] for r in c.fetchall()]

    all_relations = inbound_rels + outbound_rels
    rel_counts = Counter(all_relations)
    dominant_rel = rel_counts.most_common(1)[0][0] if rel_counts else "related"
    top_relations = [r for r, _ in rel_counts.most_common(3)]

    # Adjacent concepts: neighbors of src
    c.execute("""
        SELECT DISTINCT n.concept FROM nodes n
        JOIN edges e ON (e.dst = n.id AND e.src = ?)
                     OR (e.src = n.id AND e.dst = ?)
        WHERE n.id != ? AND n.id != ?
        LIMIT 6
    """, (src_id, src_id, src_id, dst_id))
    adjacent = [row[0] for row in c.fetchall() if row[0]]

    # Forbidden signatures near these nodes
    c.execute("SELECT signature FROM forbidden LIMIT 3")
    forbidden_adj = [row[0] for row in c.fetchall()]

    domains = list({src_domain, dst_domain} - {None, "recursion"})
    is_cross = src_domain != dst_domain

    precision = min(1.0, (
        len(adjacent) * 0.1 +
        len(top_relations) * 0.15 +
        len(forbidden_adj) * 0.2 +
        (0.3 if is_cross else 0.0)
    ))

    return {
        "src_id":             src_id,
        "dst_id":             dst_id,
        "src_concept":        src_concept  or "unknown",
        "dst_concept":        dst_concept  or "unknown",
        "src_domain":         src_domain   or "unassigned",
        "dst_domain":         dst_domain   or "unassigned",
        "hole_type":          hole_type,
        "dominant_relation":  dominant_rel,
        "top_relations":      top_relations,
        "inbound_relations":  inbound_rels,
        "outbound_relations": outbound_rels,
        "adjacent_concepts":  adjacent,
        "forbidden_adjacent": forbidden_adj,
        "n_domains":          len(domains),
        "is_cross_domain":    is_cross,
        "border_domains":     domains,
        "precision":          round(precision, 3),
    }


def find_nameable_holes(conn, limit=20):
    """
    Find structural holes in the SQLite knowledge graph.

    Detects three types and returns rich profiles ranked by precision.
    Called by driver.py as: find_nameable_holes(conn, limit=2)

    Args:
        conn  : sqlite3 connection
        limit : max profiles to return (ranked by precision, highest first)

    Returns:
        list of profile dicts
    """
    c = conn.cursor()
    c.execute("SELECT src, dst FROM edges")
    edges = c.fetchall()
    edge_set = set(edges)

    candidates = []

    # Type 1: Transitive -- a->b->c, missing a->c
    outgoing = {}
    for src, dst in edges:
        outgoing.setdefault(src, set()).add(dst)

    for a, b_set in outgoing.items():
        for b in b_set:
            for d in outgoing.get(b, set()):
                if d != a and (a, d) not in edge_set:
                    candidates.append((a, d, "transitive"))

    # Type 2: Co-citation -- c->a and c->b, missing a->b
    incoming = {}
    for src, dst in edges:
        incoming.setdefault(dst, set()).add(src)

    seen = set()
    for node, parents in incoming.items():
        parent_list = list(parents)
        for i in range(len(parent_list)):
            for j in range(i + 1, len(parent_list)):
                a, b = parent_list[i], parent_list[j]
                pair = (min(a, b), max(a, b))
                if pair not in seen and (a, b) not in edge_set and (b, a) not in edge_set:
                    seen.add(pair)
                    candidates.append((a, b, "co_citation"))

    # Type 3: Symmetry -- a->b exists but b->a missing
    for src, dst in edges:
        if (dst, src) not in edge_set:
            candidates.append((dst, src, "symmetry"))

    # Deduplicate
    seen_pairs = set()
    unique = []
    for src, dst, htype in candidates:
        if (src, dst) not in seen_pairs:
            seen_pairs.add((src, dst))
            unique.append((src, dst, htype))

    # Build profiles and rank by precision
    profiles = []
    for src_id, dst_id, htype in unique[:limit * 5]:
        profile = _build_profile(conn, src_id, dst_id, htype)
        if profile:
            profiles.append(profile)

    profiles.sort(key=lambda p: p["precision"], reverse=True)
    return profiles[:limit]


def analyze_hole(conn, src_id, dst_id):
    """
    Build a profile for a specific known hole pair.
    Called by questioner.interrogate_hole() for legacy compatibility.
    """
    return _build_profile(conn, src_id, dst_id, "named")
