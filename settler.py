"""
settler.py — Phase 4 (hardened)
The Great Discovery

═══════════════════════════════════════════════════════════════════════════════
LAPLACIAN ENERGY MINIMIZATION FOR HOLE SETTLING
═══════════════════════════════════════════════════════════════════════════════

A hole is filled by finding the concept c* that minimizes:

    E_total(c) = E_normalized(c) + E_forbidden(c)

where:

    E_normalized(c) = (1/|N|) · Σ_{v ∈ N} w(rel_type) · d(c, v)²

        w(rel_type)  = structural weight of the dominant relation type
                       (from RELATION_WEIGHTS in semantics.py)
        d(c, v)      = deterministic semantic distance between concept c
                       and the concept of node v

    E_forbidden(c) = λ · I(forbidden_sigs non-empty) · homogeneity(c, N)

        homogeneity(c, N) = count(n ∈ N where n.domain == c.domain) / |N|
        λ = 0.35 (forbidden penalty weight)

The concept c* with minimum total energy settles into the hole.

─────────────────────────────────────────────────────────────────────────────
RECURSION DOMAIN HANDLING
─────────────────────────────────────────────────────────────────────────────

Nodes with domain='recursion' carry question tokens as their concept
(e.g. "bridge:physics:mathematics:emerges_from"). These are not in the
84-concept vocabulary and cannot be directly compared using the standard
semantic distance function.

For settling purposes, recursion-domain nodes are treated as having
domain index RECURSION_DOMAIN_INDEX = 3 (cognition). This is intentional:

    - Cognition sits at the centre of the domain index ordering
      (physics=0, mathematics=1, biology=2, cognition=3, systems=4, information=5)
    - Meta-awareness, self-reference, and pattern recognition — the semantic
      territory of question nodes — align most naturally with cognition
    - Placing recursion at the centre minimises the maximum distance penalty
      from any domain, giving question nodes moderate pull from all directions
      rather than strong pull from one and weak pull from others

This is documented here so it is a choice, not an accident.

─────────────────────────────────────────────────────────────────────────────
HOLD COORDINATION WITH QUESTIONER
─────────────────────────────────────────────────────────────────────────────

When a hole has recently been questioned, its endpoint nodes receive a
pressure boost from questioner._apply_pressure_boost(). The settler
checks this boost before filling:

    If boost(src) > HOLD_THRESHOLD or boost(dst) > HOLD_THRESHOLD:
        skip this epoch — still being questioned

This prevents the settler from prematurely filling holes that the
questioner is still circling. The hold releases naturally as boost
decays at 0.15/epoch.

    HOLD_THRESHOLD = 0.3
    Boost decay rate = 0.15/epoch
    Hold duration ≈ 2 epochs after question is generated

═══════════════════════════════════════════════════════════════════════════════
"""

from semantics import RELATION_WEIGHTS, CONCEPT_VOCABULARY, DOMAIN_INDEX


# ── Constants ─────────────────────────────────────────────────────────────────
FORBIDDEN_PENALTY_WEIGHT = 0.35
HOLD_THRESHOLD           = 0.3

# Domain index assigned to recursion-domain nodes in semantic distance.
# Intentionally set to cognition (3) — see module docstring.
RECURSION_DOMAIN_INDEX   = 3


# ── Semantic distance ─────────────────────────────────────────────────────────

def _domain_index(domain):
    """
    Return the integer domain index for distance calculations.

    Known domains use their position in DOMAIN_INDEX.
    The 'recursion' domain is explicitly mapped to RECURSION_DOMAIN_INDEX (3).
    Any other unknown domain defaults to 3 (centre position).
    """
    if domain == 'recursion':
        return RECURSION_DOMAIN_INDEX
    return DOMAIN_INDEX.get(domain, 3)


def _semantic_distance(concept_a, domain_a, concept_b, domain_b):
    """
    Deterministic semantic distance between two concepts.

    d(a, b) = 0.0                          if concept_a == concept_b
    d(a, b) = 0.2                          if domain_a  == domain_b
    d(a, b) = 0.4 + |idx_a - idx_b| / 5   otherwise

    Domain index difference normalised over 5 (max possible), keeping d ∈ [0, 1].
    """
    if concept_a == concept_b:
        return 0.0
    if domain_a == domain_b:
        return 0.2
    idx_a = _domain_index(domain_a)
    idx_b = _domain_index(domain_b)
    return 0.4 + abs(idx_a - idx_b) / 5.0


# ── Hold coordination ─────────────────────────────────────────────────────────

def _get_boost(conn, node_id):
    """
    Return the current pressure boost on a node.
    Returns 0.0 if the pressure_boost column doesn't exist yet
    (questioner hasn't run) or if the node has no boost.
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
    Return True if either endpoint of a hole is currently held by the questioner.
    """
    return (_get_boost(conn, src_id) > HOLD_THRESHOLD or
            _get_boost(conn, dst_id) > HOLD_THRESHOLD)


# ── Energy computation ────────────────────────────────────────────────────────

def _dominant_relation(conn, src_id, dst_id):
    """Return the most common relation type in the local neighborhood."""
    c = conn.cursor()
    c.execute("""
        SELECT relation_type, COUNT(*) as cnt
        FROM edges
        WHERE src IN (?, ?) OR dst IN (?, ?)
        GROUP BY relation_type
        ORDER BY cnt DESC
        LIMIT 1
    """, (src_id, dst_id, src_id, dst_id))
    row = c.fetchone()
    return row[0] if row else 'related'


def _neighborhood(conn, src_id, dst_id):
    """
    Return list of (node_id, concept, domain) for all nodes in the
    local neighborhood of the hole (src, dst).
    """
    c = conn.cursor()
    c.execute("""
        SELECT DISTINCT n.id, n.concept, n.domain
        FROM nodes n
        JOIN edges e ON e.src = n.id OR e.dst = n.id
        WHERE (e.src IN (?, ?) OR e.dst IN (?, ?))
          AND n.id NOT IN (?, ?)
    """, (src_id, dst_id, src_id, dst_id, src_id, dst_id))
    return c.fetchall()


def _settling_energy(candidate_concept, candidate_domain,
                     neighborhood, rel_weight, forbidden_sigs):
    """
    Compute E_total(c) for a candidate concept.

    Args:
        candidate_concept : str
        candidate_domain  : str
        neighborhood      : list of (node_id, concept, domain)
        rel_weight        : float — weight of dominant relation type
        forbidden_sigs    : set   — current forbidden motif signatures

    Returns:
        float : E_total
    """
    if not neighborhood:
        return 0.0

    # Laplacian energy component
    energy = sum(
        rel_weight * _semantic_distance(
            candidate_concept, candidate_domain,
            nbr_concept, nbr_domain
        ) ** 2
        for (_, nbr_concept, nbr_domain) in neighborhood
    )
    e_normalized = energy / len(neighborhood)

    # Forbidden penalty component
    if forbidden_sigs:
        same_domain_count = sum(
            1 for (_, _, nbr_domain) in neighborhood
            if nbr_domain == candidate_domain
        )
        homogeneity = same_domain_count / len(neighborhood)
        e_forbidden = FORBIDDEN_PENALTY_WEIGHT * homogeneity
    else:
        e_forbidden = 0.0

    return e_normalized + e_forbidden


# ── Urgency ───────────────────────────────────────────────────────────────────

def _urgency(conn, src_id, dst_id):
    """
    Urgency score for filling a hole — higher for low-degree nodes.

        urgency(a, d) = 1/(1 + deg(a)·0.2) + 1/(1 + deg(d)·0.2)

    Low-degree nodes are structurally more isolated and their holes
    are more likely to be genuine structural demands.
    """
    c = conn.cursor()
    c.execute("""
        SELECT COUNT(*) FROM (
            SELECT src AS node_id FROM edges WHERE src = ?
            UNION ALL
            SELECT dst AS node_id FROM edges WHERE dst = ?
        )
    """, (src_id, src_id))
    deg_src = c.fetchone()[0]

    c.execute("""
        SELECT COUNT(*) FROM (
            SELECT src AS node_id FROM edges WHERE src = ?
            UNION ALL
            SELECT dst AS node_id FROM edges WHERE dst = ?
        )
    """, (dst_id, dst_id))
    deg_dst = c.fetchone()[0]

    return 1.0 / (1.0 + deg_src * 0.2) + 1.0 / (1.0 + deg_dst * 0.2)


# ── Concept finding ───────────────────────────────────────────────────────────

def find_settling_concept(conn, src_id, dst_id):
    """
    Find the concept that minimizes settling energy for hole (src, dst).

    Exhaustively scores all 84 vocabulary concepts and returns the
    minimum-energy candidate.

    Returns:
        (concept, domain, energy) or (None, None, None) if no neighborhood
    """
    neighborhood = _neighborhood(conn, src_id, dst_id)
    if not neighborhood:
        return None, None, None

    rel_type   = _dominant_relation(conn, src_id, dst_id)
    rel_weight = RELATION_WEIGHTS.get(rel_type, 0.7)

    c = conn.cursor()
    c.execute("SELECT signature FROM forbidden")
    forbidden_sigs = set(row[0] for row in c.fetchall())

    best_concept = None
    best_domain  = None
    best_energy  = float('inf')

    for (concept, domain) in CONCEPT_VOCABULARY:
        e = _settling_energy(concept, domain,
                             neighborhood, rel_weight, forbidden_sigs)
        if e < best_energy:
            best_energy  = e
            best_concept = concept
            best_domain  = domain

    return best_concept, best_domain, best_energy


# ── Main settling entry point ─────────────────────────────────────────────────

def settle_holes(conn, epoch, limit=3):
    """
    Fill up to `limit` open holes per epoch.

    Selection order: highest urgency first (lowest-degree endpoints).
    Holes currently held by the questioner (pressure_boost > HOLD_THRESHOLD)
    are skipped.

    For each selected hole:
        1. Find minimum-energy settling concept
        2. Insert concept as a new node
        3. Add edges (src → new, new → dst)
        4. Mark hole as filled in the holes table

    Args:
        conn  : SQLite connection
        epoch : int — current epoch
        limit : int — maximum holes to fill (default 3,
                      reduced to 1 when EXPANDING,
                      0 when mismatch ≥ HALT_THRESHOLD)
    """
    c = conn.cursor()

    c.execute("""
        SELECT src_id, dst_id FROM holes
        WHERE filled = 0
        ORDER BY rowid ASC
    """)
    open_holes = c.fetchall()

    if not open_holes:
        return

    # Sort by urgency, skip held holes
    candidates = []
    for (src_id, dst_id) in open_holes:
        if _is_held(conn, src_id, dst_id):
            continue
        urgency = _urgency(conn, src_id, dst_id)
        candidates.append((urgency, src_id, dst_id))

    candidates.sort(reverse=True)

    settled = 0
    for (urgency, src_id, dst_id) in candidates:
        if settled >= limit:
            break

        concept, domain, energy = find_settling_concept(conn, src_id, dst_id)
        if concept is None:
            continue

        # Insert settled node
        c.execute(
            "INSERT INTO nodes (concept, domain, introduced) VALUES (?, ?, ?)",
            (concept, domain, epoch)
        )
        new_id = c.lastrowid

        # Connect into hole
        from semantics import relation_weight
        c.execute("INSERT INTO edges VALUES (?, ?, ?, ?)",
                  (src_id, new_id, 'requires',    relation_weight('requires')))
        c.execute("INSERT INTO edges VALUES (?, ?, ?, ?)",
                  (new_id, dst_id, 'emerges_from', relation_weight('emerges_from')))

        # Mark hole filled
        c.execute("""
            UPDATE holes SET filled = 1, filled_by = ?, filled_epoch = ?
            WHERE src_id = ? AND dst_id = ?
        """, (new_id, epoch, src_id, dst_id))

        conn.commit()
        settled += 1
