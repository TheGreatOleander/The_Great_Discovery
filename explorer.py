"""
explorer.py — Phase 3 (hardened)
The Great Discovery

═══════════════════════════════════════════════════════════════════════════════
MATHEMATICS — PRESSURE FIELD WITH FORBIDDEN REPULSION AND HOLE ATTRACTION
═══════════════════════════════════════════════════════════════════════════════

THE PREVIOUS IMPLEMENTATION:
    build_pressure_field() computed a net pull/void/push score per node but
    the forbidden and holes tables were not consulted during exploration.
    The engine knew where the walls were and ignored them. New nodes were
    placed without regard for where the structural pressure was actually
    highest. The governance loop was open on the exploration side.

THE FIX — THREE-FORCE PRESSURE FIELD:

    For each node v, the net pressure field value is:

        field(v) = pull(v) + void(v) + hole_attraction(v) - forbidden_repulsion(v)

    1. PULL — degree-based attraction
       pull(v) = deg(v) / max_deg
       High-degree nodes attract new connections (hub gravity).

    2. VOID — structural underrepresentation
       void(v) = (1 - deg(v) / (deg(v) + implied_missing(v))) * (1 / (1 + deg(v)*0.3))
       implied_missing: edges that transitively should exist but don't.
       Nodes with many implied-but-missing edges are structurally hungry.

    3. HOLE ATTRACTION — pull toward open, ripe holes
       For each open hole (src, dst) in the holes table:
           If v is src or dst: add hole_weight * precision
           If v is in the neighborhood: add hole_weight * precision * 0.3
       hole_weight = 0.6 (tunable)
       precision   = hole's structural precision score (0 to 1)

       Justification: holes with high precision are structurally well-defined.
       Exploring near them gives the engine more constraints to work with,
       producing better-shaped questions on subsequent epochs.

    4. FORBIDDEN REPULSION — push away from destabilizing patterns
       For each forbidden motif, identify nodes whose neighborhoods most
       closely match that forbidden pattern. Apply a repulsion penalty:

           repulsion(v) = forbidden_push * (deg(v) / max_deg) * proximity_score(v)

       proximity_score(v) = fraction of v's edges that participate in
                            forbidden-similar motifs (approximated by
                            checking if v's degree puts it in the
                            homogeneous zone that produced the spike).

       forbidden_push = 0.4 * spike_magnitude (from forbidden table)

       This means: nodes in highly connected, homogeneous clusters get
       pushed down in the field. New nodes are steered away from recreating
       the structural configurations that caused governance spikes.

SOFTMAX SAMPLING:
    The field is converted to a probability distribution via softmax with
    temperature T:

        p(v) = exp(field(v) / T) / Z

    Low T (0.2): sharply peaked — strongly favors highest-pressure nodes.
    High T (0.8): flatter — more exploration of moderate-pressure nodes.

    Default T = 0.4. When the engine is in DIVERGENT state the driver
    should pass T = 0.6 to increase exploration diversity.

═══════════════════════════════════════════════════════════════════════════════
"""

import random
import math
from semantics import sample_concept, sample_relation, relation_weight


# ── Pressure field constants ──────────────────────────────────────────────────
HOLE_ATTRACTION_WEIGHT  = 0.6   # Attraction toward open, precise holes
FORBIDDEN_PUSH_SCALE    = 0.4   # Scale factor on spike magnitude for repulsion
VOID_WEIGHT             = 1.4   # Weight on structural void tension
SEMANTIC_PULL_WEIGHT    = 0.8   # Weight on domain underrepresentation pull


def build_pressure_field(conn, temperature=0.4):
    """
    Compute the three-force pressure field over all nodes.

    Forces:
        pull(v)              — degree-based hub gravity
        void(v)              — structural underrepresentation tension
        hole_attraction(v)   — pull toward open, precise holes
        forbidden_repulsion(v) — push away from forbidden-adjacent zones

    Returns dict: {node_id: field_value}, all values > 0.
    """
    c = conn.cursor()

    c.execute("SELECT id, concept, domain FROM nodes")
    all_nodes = {row[0]: {'concept': row[1], 'domain': row[2]} for row in c.fetchall()}
    if not all_nodes:
        return {}

    c.execute("SELECT src, dst, relation_type, weight FROM edges")
    edges    = c.fetchall()
    edge_set = set((a, b) for (a, b, _, _) in edges)

    # ── Degree and domain statistics ──────────────────────────────────────────
    degree = {}
    for (a, b, _, _) in edges:
        degree[a] = degree.get(a, 0) + 1
        degree[b] = degree.get(b, 0) + 1
    max_degree = max(degree.values(), default=1)

    domain_counts = {}
    for nid, nd in all_nodes.items():
        d = nd['domain']
        domain_counts[d] = domain_counts.get(d, 0) + 1
    max_domain_count = max(domain_counts.values(), default=1)

    # ── Forbidden motif data ──────────────────────────────────────────────────
    # Load forbidden signatures and their spike magnitudes
    c.execute("SELECT signature, spike_score FROM forbidden")
    forbidden_rows  = c.fetchall()
    forbidden_sigs  = {row[0]: row[1] for row in forbidden_rows}   # sig -> spike
    total_spike     = sum(forbidden_sigs.values()) if forbidden_sigs else 0.0

    # ── Hole attraction data ──────────────────────────────────────────────────
    # Open (unfilled) holes with their shape signatures
    # We parse src/dst from shape_sig format "src_id-bridge_id-dst_id"
    c.execute("SELECT shape_sig FROM holes WHERE filled=0")
    open_hole_sigs = [row[0] for row in c.fetchall()]

    # Also pull precision from questioner-generated holes logged in the
    # holes table. We approximate precision from the question log if available.
    # For now: open holes all contribute equally with weight HOLE_ATTRACTION_WEIGHT
    hole_node_weights = {}   # node_id -> cumulative attraction weight
    for sig in open_hole_sigs:
        parts = sig.replace('hole:', '').split('->')
        if len(parts) == 2:
            # Format: "hole:src->dst"
            try:
                src_id = int(parts[0])
                dst_id = int(parts[1])
                hole_node_weights[src_id] = hole_node_weights.get(src_id, 0) + HOLE_ATTRACTION_WEIGHT
                hole_node_weights[dst_id] = hole_node_weights.get(dst_id, 0) + HOLE_ATTRACTION_WEIGHT
                # Neighborhood nodes get a softer pull
                for (a, b, _, _) in edges:
                    if a in (src_id, dst_id):
                        hole_node_weights[b] = hole_node_weights.get(b, 0) + HOLE_ATTRACTION_WEIGHT * 0.3
                    if b in (src_id, dst_id):
                        hole_node_weights[a] = hole_node_weights.get(a, 0) + HOLE_ATTRACTION_WEIGHT * 0.3
            except ValueError:
                pass
        else:
            # Format: "a-bridge-d"
            try:
                ids = [int(x) for x in sig.split('-')]
                if len(ids) >= 2:
                    hole_node_weights[ids[0]] = hole_node_weights.get(ids[0], 0) + HOLE_ATTRACTION_WEIGHT
                    hole_node_weights[ids[-1]] = hole_node_weights.get(ids[-1], 0) + HOLE_ATTRACTION_WEIGHT
            except ValueError:
                pass

    # ── Per-node field computation ────────────────────────────────────────────
    field = {}
    for n, ndata in all_nodes.items():
        deg  = degree.get(n, 0)
        pull = deg / max_degree

        # Void tension: how many implied-but-missing edges does this node have?
        neighbors = set()
        for (a, b, _, _) in edges:
            if a == n: neighbors.add(b)
            if b == n: neighbors.add(a)

        implied_missing = 0
        for nb in neighbors:
            for (a2, b2, _, _) in edges:
                if a2 == nb and b2 != n and (n, b2) not in edge_set:
                    implied_missing += 1

        void = (
            1.0 if deg == 0
            else (1.0 - deg / max(deg + implied_missing, 1)) * (1.0 / (1.0 + deg * 0.3))
        )

        # Semantic pull: underrepresented domains attract more exploration
        domain_rep   = domain_counts.get(ndata['domain'], 1) / max_domain_count
        semantic_pull = 1.0 - domain_rep

        # Hole attraction: nodes near open, precise holes get a bonus
        hole_attr = hole_node_weights.get(n, 0.0)

        # Forbidden repulsion: nodes in high-degree, homogeneous clusters
        # (the structural signature of forbidden motifs) get pushed down
        repulsion = 0.0
        if forbidden_sigs and deg > max_degree * 0.6:
            # Proximity score: how much of this node's neighborhood looks
            # like the configurations that caused governance spikes?
            # Approximation: high-degree nodes in homogeneous domain clusters
            # are most likely to recreate forbidden patterns.
            nbr_domains = [all_nodes[nb]['domain'] for nb in neighbors if nb in all_nodes]
            if nbr_domains:
                same_domain_frac = nbr_domains.count(ndata['domain']) / len(nbr_domains)
            else:
                same_domain_frac = 0.0

            # Scale repulsion by total spike magnitude accumulated
            # (more forbidden motifs = stronger repulsion signal)
            avg_spike  = total_spike / len(forbidden_sigs) if forbidden_sigs else 0.0
            repulsion  = FORBIDDEN_PUSH_SCALE * avg_spike * same_domain_frac * (deg / max_degree)

        net = (pull
               + void          * VOID_WEIGHT
               + semantic_pull * SEMANTIC_PULL_WEIGHT
               + hole_attr
               - repulsion)

        field[n] = max(net, 0.001)

    return field


def sample_from_field(field, temperature=0.4):
    """
    Softmax sampling over the pressure field.

        p(v) = exp(field(v) / T) / Z

    Lower temperature = sharper peak toward highest-pressure nodes.
    Higher temperature = more uniform exploration.

    Args:
        field       : dict {node_id: pressure_value}
        temperature : float, default 0.4

    Returns:
        node_id of sampled node
    """
    if not field:
        return None

    nodes  = list(field.keys())
    scores = [field[n] for n in nodes]
    max_s  = max(scores)
    exps   = [math.exp((s - max_s) / temperature) for s in scores]
    total  = sum(exps)
    probs  = [e / total for e in exps]

    r          = random.random()
    cumulative = 0.0
    for node, prob in zip(nodes, probs):
        cumulative += prob
        if r <= cumulative:
            return node
    return nodes[-1]


def explore(conn, bias_strength=0.7, epoch=0, temperature=0.4):
    """
    Grow the graph by one typed node per epoch.

    Placement is biased toward the highest-pressure region of the field:
    - Pulled toward nodes near open holes (unexplored structural demands)
    - Pulled toward structurally underrepresented regions
    - Repelled from forbidden-adjacent zones

    Args:
        conn          : SQLite connection
        bias_strength : float — probability of using field-biased placement
                        vs random placement (default 0.7)
        epoch         : int — current epoch (recorded on node)
        temperature   : float — softmax temperature for field sampling
                        (pass higher value when engine is in DIVERGENT state)
    """
    c = conn.cursor()

    concept, domain = sample_concept()
    c.execute(
        "INSERT INTO nodes (concept, domain, introduced) VALUES (?, ?, ?)",
        (concept, domain, epoch)
    )
    new_id = c.lastrowid

    c.execute("SELECT id, domain FROM nodes WHERE id != ?", (new_id,))
    existing = [(row[0], row[1]) for row in c.fetchall()]

    if existing:
        if random.random() < bias_strength:
            field = build_pressure_field(conn, temperature=temperature)
            field.pop(new_id, None)
            target_id = sample_from_field(field, temperature=temperature) if field else existing[0][0]
            target_domain = next((d for nid, d in existing if nid == target_id), 'unassigned')
        else:
            target_id, target_domain = random.choice(existing)

        relation = sample_relation(domain, target_domain)
        weight   = relation_weight(relation)
        c.execute(
            "INSERT INTO edges VALUES (?, ?, ?, ?)",
            (new_id, target_id, relation, weight)
        )

    conn.commit()


def allocate_holes(conn, epoch=0, limit=3, src_id=None, dst_id=None):
    """
    Fill holes via energy minimization.

    If src_id and dst_id are specified, fill that specific hole.
    Otherwise fill the top-urgency holes (general settling pass).
    """
    from settler import settle_holes, settle_specific_hole

    if src_id is not None and dst_id is not None:
        return settle_specific_hole(conn, epoch, src_id, dst_id)
    else:
        return settle_holes(conn, epoch, limit=limit)