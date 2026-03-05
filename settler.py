"""
settler.py — Phase 3 hardened v2
The Great Discovery

═══════════════════════════════════════════════════════════════════════════════
SETTLER / QUESTIONER COORDINATION
═══════════════════════════════════════════════════════════════════════════════

THE PROBLEM:
    When a question is asked about a hole H(src, dst), a pressure boost is
    applied to src and dst. The boost signals: "this hole is still gathering
    constraints — don't settle it yet." But settle_holes() was filling holes
    indiscriminately, including ones actively being questioned.

    A questioned hole filled too early produces a low-confidence settlement.
    The whole point of the boost is to let the topology accumulate more
    constraint around the hole before the settler commits. Filling it early
    throws that away.

THE FIX — HOLD OPEN QUESTIONED HOLES:
    Before settling any hole at (a, d), check whether either endpoint has
    an active pressure boost above HOLD_THRESHOLD. If so, skip it this epoch.

    HOLD_THRESHOLD = 0.3

    Justification: a fresh question produces boost = precision × 1.2 ≈ 0.9.
    After ~4 epochs of decay (4 × 0.15 = 0.6), boost ≈ 0.3. At that point
    the engine has had time to explore the region and accumulate constraints.
    Below HOLD_THRESHOLD, the hold releases and the settler fills the hole
    with a better-informed energy minimum.

    This means: the quality of settlement improves with question age.
    The longer a question has been open (up to the hold threshold), the more
    constrained the hole becomes, and the lower the settling energy of the
    winning concept.

URGENCY FORMULA (unchanged from v1):
    urgency(a, d) = 1/(1 + deg(a)·0.2) + 1/(1 + deg(d)·0.2)

    Low-degree nodes are more urgent — structurally isolated, filling their
    hole has larger normalizing effect on the pressure field.

FULL-VOCABULARY ENERGY MINIMIZATION (unchanged from v1):
    Score all 84 vocabulary concepts exhaustively.
    c* = argmin E_total(c) = E_laplacian(c) + E_forbidden(c)
    See v1 docstring §6 for full derivation.

═══════════════════════════════════════════════════════════════════════════════
"""

import math
import random
from collections import Counter
from semantics import (
    ALL_CONCEPTS, sample_relation, relation_weight,
    semantic_distance, describe_hole_demand, RELATION_WEIGHTS
)

HOLD_THRESHOLD = 0.3   # Boost level above which a hole is held open


# ─── Energy computation (unchanged) ──────────────────────────────────────────

def _domain_embedding(domain):
    DOMAIN_ORDER = {
        'physics': 0, 'mathematics': 1, 'biology': 2,
        'cognition': 3, 'systems': 4, 'information': 5
    }
    return DOMAIN_ORDER.get(domain, 3)


def _semantic_distance_fast(concept_a, domain_a, concept_b, domain_b):
    """
    Deterministic semantic distance for stable energy minimization.
        d = 0.0                     if same concept
        d = 0.2                     if same domain
        d = 0.4 + |Δidx| / 5       if cross-domain
    """
    if concept_a == concept_b:
        return 0.0
    if domain_a == domain_b:
        return 0.2
    da = _domain_embedding(domain_a)
    db = _domain_embedding(domain_b)
    return 0.4 + abs(da - db) / 5.0


def _laplacian_energy(concept, domain, surrounding_nodes, surrounding_relations):
    """
    E(c) = (1/|N|) Σ_{v∈N} w(rel) · d(c,v)²

    Laplacian quadratic form normalized by neighborhood size.
    """
    if not surrounding_nodes:
        return 0.5
    rel_counts   = Counter(surrounding_relations)
    dominant_rel = rel_counts.most_common(1)[0][0] if rel_counts else 'related'
    w            = RELATION_WEIGHTS.get(dominant_rel, 0.5)
    energy = sum(w * (_semantic_distance_fast(concept, domain,
                                               n['concept'], n['domain']) ** 2)
                 for n in surrounding_nodes)
    return energy / len(surrounding_nodes)


def _forbidden_penalty(domain, surrounding_nodes, forbidden_sigs, lambda_=0.35):
    """
    penalty = λ · I(forbidden non-empty) · domain_homogeneity
    """
    if not forbidden_sigs or not surrounding_nodes:
        return 0.0
    domain_list = [n['domain'] for n in surrounding_nodes]
    homogeneity = sum(1 for d in domain_list if d == domain) / len(domain_list)
    return lambda_ * homogeneity


def settling_energy(concept, domain, surrounding_nodes, surrounding_relations, forbidden_sigs):
    """
    E_total(c) = E_laplacian(c) + E_forbidden(c)
    Lower = better fit.
    """
    return (_laplacian_energy(concept, domain, surrounding_nodes, surrounding_relations)
            + _forbidden_penalty(domain, surrounding_nodes, forbidden_sigs))


def find_settling_concept(surrounding_nodes, surrounding_relations, forbidden_sigs):
    """
    Exhaustive search over all 84 vocabulary concepts.
    Returns (concept, domain, energy) with minimum total energy.
    """
    if not ALL_CONCEPTS:
        return 'unknown', 'unassigned', 1.0
    best_concept, best_domain, best_energy = None, None, math.inf
    for concept, domain in ALL_CONCEPTS:
        e = settling_energy(concept, domain, surrounding_nodes,
                            surrounding_relations, forbidden_sigs)
        if e < best_energy:
            best_energy  = e
            best_concept = concept
            best_domain  = domain
    return best_concept, best_domain, best_energy


# ─── Pressure boost query ─────────────────────────────────────────────────────

def _get_boost(conn, node_id):
    """
    Return the current pressure_boost for a node, or 0.0 if column
    doesn't exist yet or node has no boost.
    """
    c = conn.cursor()
    try:
        c.execute("SELECT pressure_boost FROM nodes WHERE id = ?", (node_id,))
        row = c.fetchone()
        return row[0] if row and row[0] is not None else 0.0
    except Exception:
        return 0.0


def _is_held(conn, src_id, dst_id):
    """
    Return True if either endpoint of hole (src, dst) has a pressure boost
    above HOLD_THRESHOLD — meaning the hole is still being questioned and
    should not be settled yet.
    """
    return (_get_boost(conn, src_id) > HOLD_THRESHOLD or
            _get_boost(conn, dst_id) > HOLD_THRESHOLD)


# ─── Neighborhood gathering ───────────────────────────────────────────────────

def _gather_neighborhood(conn, src_id, dst_id, edge_set, node_data):
    c = conn.cursor()
    neighborhood_ids = set()
    for (a, b) in edge_set:
        if a in (src_id, dst_id) or b in (src_id, dst_id):
            neighborhood_ids.add(a)
            neighborhood_ids.add(b)
    neighborhood_ids -= {src_id, dst_id}
    surrounding_nodes = [node_data[n] for n in neighborhood_ids if n in node_data]
    if neighborhood_ids:
        placeholders = ','.join('?' * len(neighborhood_ids))
        ids = list(neighborhood_ids)
        c.execute(
            f"SELECT relation_type FROM edges WHERE src IN ({placeholders}) OR dst IN ({placeholders})",
            ids + ids
        )
        surrounding_relations = [row[0] for row in c.fetchall()]
    else:
        surrounding_relations = []
    return surrounding_nodes, surrounding_relations


# ─── Main settling pass ───────────────────────────────────────────────────────

def settle_holes(conn, epoch, limit=3):
    """
    Find highest-urgency holes and settle minimum-energy concepts into them.

    Holes with active pressure boosts above HOLD_THRESHOLD are skipped —
    they are still being questioned and need more time to accumulate constraints.

    Returns list of settled hole records.
    """
    c = conn.cursor()
    c.execute("SELECT src, dst FROM edges")
    raw_edges = c.fetchall()
    edge_set  = set(raw_edges)
    if not raw_edges:
        return []

    c.execute("SELECT id, concept, domain FROM nodes")
    node_data = {row[0]: {'concept': row[1], 'domain': row[2]} for row in c.fetchall()}

    c.execute("SELECT signature FROM forbidden")
    forbidden_sigs = set(row[0] for row in c.fetchall())

    degree = {}
    for (a, b) in raw_edges:
        degree[a] = degree.get(a, 0) + 1
        degree[b] = degree.get(b, 0) + 1

    # Collect transitive hole candidates with urgency scores
    hole_candidates = []
    for (a, b) in raw_edges:
        for (b2, d) in raw_edges:
            if b == b2 and (a, d) not in edge_set and a != d:
                urgency = (1.0 / (1.0 + degree.get(a, 0) * 0.2) +
                           1.0 / (1.0 + degree.get(d, 0) * 0.2))
                hole_candidates.append((urgency, a, b, d))

    if not hole_candidates:
        return []

    hole_candidates.sort(key=lambda x: x[0], reverse=True)
    to_settle = hole_candidates[:limit * 2]
    random.shuffle(to_settle)

    settled  = []
    inserted = 0

    for urgency, a, bridge, d in to_settle:
        if inserted >= limit:
            break
        if (a, d) in edge_set:
            continue

        # ── COORDINATION: skip held holes ─────────────────────────────────────
        if _is_held(conn, a, d):
            continue   # Still being questioned — let boost decay first

        surrounding_nodes, surrounding_relations = _gather_neighborhood(
            conn, a, d, edge_set, node_data
        )

        concept, domain, energy = find_settling_concept(
            surrounding_nodes, surrounding_relations, forbidden_sigs
        )

        src_domain = node_data.get(a, {}).get('domain', 'unassigned')
        dst_domain = node_data.get(d, {}).get('domain', 'unassigned')
        relation   = sample_relation(src_domain, dst_domain)
        weight     = relation_weight(relation)

        c.execute("INSERT INTO edges VALUES (?, ?, ?, ?)", (a, d, relation, weight))
        edge_set.add((a, d))

        demand = describe_hole_demand(
            [n['domain'] for n in surrounding_nodes],
            surrounding_relations
        )
        c.execute("""
            INSERT INTO holes (epoch_found, shape_sig, demands, filled, filled_by)
            VALUES (?, ?, ?, 1, ?)
        """, (epoch, f"{a}-{bridge}-{d}", demand, f"{concept} ({domain})"))

        settled.append({
            'src': a, 'dst': d,
            'concept': concept, 'domain': domain,
            'energy': energy, 'demand': demand,
            'relation': relation
        })
        inserted += 1

    conn.commit()
    return settled


def settle_specific_hole(conn, epoch, src_id, dst_id):
    """
    Settle a specific hole by src and dst IDs.
    Respects the hold check — returns None if hole is still held.
    """
    if _is_held(conn, src_id, dst_id):
        return None   # Hold active — not yet

    c = conn.cursor()
    c.execute("SELECT src, dst FROM edges")
    edge_set = set(c.fetchall())
    if (src_id, dst_id) in edge_set:
        return None

    c.execute("SELECT id, concept, domain FROM nodes")
    node_data = {row[0]: {'concept': row[1], 'domain': row[2]} for row in c.fetchall()}

    c.execute("SELECT signature FROM forbidden")
    forbidden_sigs = set(row[0] for row in c.fetchall())

    surrounding_nodes, surrounding_relations = _gather_neighborhood(
        conn, src_id, dst_id, edge_set, node_data
    )

    concept, domain, energy = find_settling_concept(
        surrounding_nodes, surrounding_relations, forbidden_sigs
    )

    src_domain = node_data.get(src_id, {}).get('domain', 'unassigned')
    dst_domain = node_data.get(dst_id, {}).get('domain', 'unassigned')
    relation   = sample_relation(src_domain, dst_domain)
    weight     = relation_weight(relation)

    c.execute("INSERT INTO edges VALUES (?, ?, ?, ?)", (src_id, dst_id, relation, weight))

    demand = describe_hole_demand(
        [n['domain'] for n in surrounding_nodes],
        surrounding_relations
    )
    c.execute("""
        UPDATE holes SET filled=1, filled_by=?
        WHERE shape_sig=? AND filled=0
    """, (f"{concept} ({domain})", f"hole:{src_id}->{dst_id}"))

    conn.commit()
    return {
        'src': src_id, 'dst': dst_id,
        'concept': concept, 'domain': domain,
        'energy': energy, 'demand': demand,
        'relation': relation
    }