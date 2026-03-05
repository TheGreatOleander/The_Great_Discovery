"""
explorer.py — Phase 4 (hardened)
The Great Discovery

═══════════════════════════════════════════════════════════════════════════════
THREE-FORCE PRESSURE FIELD WITH FORBIDDEN REPULSION AND HOLE ATTRACTION
═══════════════════════════════════════════════════════════════════════════════

For each node v, the net pressure field value is:

    field(v) = pull(v) + void(v) + hole_attraction(v) - forbidden_repulsion(v)

1. PULL — degree-based hub gravity
   pull(v) = deg(v) / max_deg

2. VOID — structural underrepresentation tension
   void(v) = (1 - deg/(deg+implied_missing)) · (1/(1 + deg·0.3))
   Nodes with many implied-but-missing edges are structurally hungry.

3. HOLE ATTRACTION — pull toward open, precise holes
   For each open hole (src, dst):
       endpoint nodes: +HOLE_ATTRACTION_WEIGHT
       neighborhood nodes: +HOLE_ATTRACTION_WEIGHT × 0.3
   Attraction applies to all shape_sig formats written by any module.

4. FORBIDDEN REPULSION — push away from destabilizing patterns
   Nodes in high-degree, homogeneous domain clusters get pushed down.
   repulsion(v) = FORBIDDEN_PUSH_SCALE × avg_spike × same_domain_frac × (deg/max_deg)

SOFTMAX SAMPLING:
    p(v) = exp(field(v) / T) / Z
    T=0.4 default. Higher T from driver when engine is DIVERGENT/DEADLOCKED.

─────────────────────────────────────────────────────────────────────────────
HOLE SHAPE_SIG FORMATS
─────────────────────────────────────────────────────────────────────────────

Different modules write shape_sig in different formats. All are handled:

    "hole:{src}->{dst}"     — hole_monitor.py (retired, retained for compat)
    "{src}-{bridge}-{dst}"  — settler.py
    "{src}-{dst}"           — questioner.py
    "meta:{src}-{dst}"      — questioner.py (meta-questions)

═══════════════════════════════════════════════════════════════════════════════
"""

import random
import math
from semantics import sample_concept, sample_relation, relation_weight


HOLE_ATTRACTION_WEIGHT  = 0.6
FORBIDDEN_PUSH_SCALE    = 0.4
VOID_WEIGHT             = 1.4
SEMANTIC_PULL_WEIGHT    = 0.8


def _parse_hole_node_ids(shape_sig):
    """
    Parse (src_id, dst_id) from a hole's shape_sig.

    Handles all formats written across the codebase:
        "hole:{src}->{dst}"     hole_monitor format
        "meta:{src}-{dst}"      meta-question format
        "{src}-{bridge}-{dst}"  settler format
        "{src}-{dst}"           questioner format

    Returns (int, int) or None if unparseable.
    """
    sig = shape_sig.strip()

    if sig.startswith("hole:") and "->" in sig:
        parts = sig[5:].split("->")
        if len(parts) == 2:
            try:
                return int(parts[0]), int(parts[1])
            except ValueError:
                return None

    if sig.startswith("meta:"):
        parts = sig[5:].split("-")
        if len(parts) == 2:
            try:
                return int(parts[0]), int(parts[1])
            except ValueError:
                return None

    if "->" not in sig and not sig.startswith(("hole:", "meta:")):
        parts = sig.split("-")
        if len(parts) == 3:
            try:
                return int(parts[0]), int(parts[2])
            except ValueError:
                return None
        elif len(parts) == 2:
            try:
                return int(parts[0]), int(parts[1])
            except ValueError:
                return None

    return None


def build_pressure_field(conn, temperature=0.4):
    """
    Compute the three-force pressure field over all nodes.

    Returns dict: {node_id: field_value}, all values > 0.
    """
    c = conn.cursor()

    c.execute("SELECT id, concept, domain FROM nodes")
    all_nodes = {row[0]: {'concept': row[1], 'domain': row[2]}
                 for row in c.fetchall()}
    if not all_nodes:
        return {}

    c.execute("SELECT src, dst, relation_type, weight FROM edges")
    edges    = c.fetchall()
    edge_set = set((a, b) for (a, b, _, _) in edges)

    # Degree and domain statistics
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

    # Forbidden motif data
    c.execute("SELECT signature, spike_score FROM forbidden")
    forbidden_rows = c.fetchall()
    forbidden_sigs = {row[0]: row[1] for row in forbidden_rows}
    total_spike    = sum(forbidden_sigs.values()) if forbidden_sigs else 0.0

    # Hole attraction — load all open holes, parse endpoint IDs
    c.execute("SELECT shape_sig FROM holes WHERE filled=0")
    open_hole_sigs = [row[0] for row in c.fetchall()]

    hole_node_weights = {}
    for sig in open_hole_sigs:
        parsed = _parse_hole_node_ids(sig)
        if parsed is None:
            continue
        src_id, dst_id = parsed
        hole_node_weights[src_id] = hole_node_weights.get(src_id, 0) + HOLE_ATTRACTION_WEIGHT
        hole_node_weights[dst_id] = hole_node_weights.get(dst_id, 0) + HOLE_ATTRACTION_WEIGHT
        for (a, b, _, _) in edges:
            if a in (src_id, dst_id):
                hole_node_weights[b] = hole_node_weights.get(b, 0) + HOLE_ATTRACTION_WEIGHT * 0.3
            if b in (src_id, dst_id):
                hole_node_weights[a] = hole_node_weights.get(a, 0) + HOLE_ATTRACTION_WEIGHT * 0.3

    # Per-node field computation
    field = {}
    for n, ndata in all_nodes.items():
        deg  = degree.get(n, 0)
        pull = deg / max_degree

        neighbors = set()
        for (a, b, _, _) in edges:
            if a == n: neighbors.add(b)
            if b == n: neighbors.add(a)

        implied_missing = sum(
            1 for nb in neighbors
            for (a2, b2, _, _) in edges
            if a2 == nb and b2 != n and (n, b2) not in edge_set
        )

        void = (
            1.0 if deg == 0
            else (1.0 - deg / max(deg + implied_missing, 1)) * (1.0 / (1.0 + deg * 0.3))
        )

        domain_rep    = domain_counts.get(ndata['domain'], 1) / max_domain_count
        semantic_pull = 1.0 - domain_rep
        hole_attr     = hole_node_weights.get(n, 0.0)

        repulsion = 0.0
        if forbidden_sigs and deg > max_degree * 0.6:
            nbr_domains = [all_nodes[nb]['domain']
                           for nb in neighbors if nb in all_nodes]
            if nbr_domains:
                same_domain_frac = nbr_domains.count(ndata['domain']) / len(nbr_domains)
            else:
                same_domain_frac = 0.0
            avg_spike = total_spike / len(forbidden_sigs)
            repulsion = FORBIDDEN_PUSH_SCALE * avg_spike * same_domain_frac * (deg / max_degree)

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

    Placement is biased toward the highest-pressure region:
    pulled toward open holes, repelled from forbidden-adjacent zones,
    drawn toward structurally underrepresented domains.

    Args:
        conn          : SQLite connection
        bias_strength : float — probability of field-biased vs random placement
        epoch         : int   — current epoch (recorded on node)
        temperature   : float — softmax temperature
                        Higher when DIVERGENT or DEADLOCKED (more exploration)
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
            target_id = (sample_from_field(field, temperature=temperature)
                         if field else existing[0][0])
            target_domain = next(
                (d for nid, d in existing if nid == target_id),
                'unassigned'
            )
        else:
            target_id, target_domain = random.choice(existing)

        relation = sample_relation(domain, target_domain)
        weight   = relation_weight(relation)
        c.execute(
            "INSERT INTO edges VALUES (?, ?, ?, ?)",
            (new_id, target_id, relation, weight)
        )

    conn.commit()
