"""
governance.py — Phase 3 hardened v2
The Great Discovery

═══════════════════════════════════════════════════════════════════════════════
DOMAIN-AWARE FORBIDDEN MOTIFS
═══════════════════════════════════════════════════════════════════════════════

PREVIOUS IMPLEMENTATION:
    Forbidden motifs stored (signature, spike_score) only.
    Two forbidden motifs — one from physics/mathematics boundary, one from
    cognition/systems — were treated identically by the repulsion field.
    The repulsion was applied globally: any high-degree homogeneous cluster
    got pushed down, regardless of which domain boundary produced the spike.

    This is imprecise. A forbidden pattern in physics/mathematics says nothing
    about whether cognition/systems configurations are dangerous. The engine
    was over-cautious in unrelated regions and under-cautious in the specific
    domain context where the spike actually occurred.

THE FIX — DOMAIN CONTEXT ON FORBIDDEN MOTIFS:

    Forbidden motifs now carry:
        signature    — isomorphism-invariant structural signature (unchanged)
        spike_score  — magnitude of the compression spike (unchanged)
        domain_set   — the set of domains present in the subgraph at spike time
                       stored as comma-separated sorted string, e.g. "mathematics,physics"
        epoch_found  — epoch of the spike

    The forbidden table gains two new columns (added via ALTER TABLE, idempotent).

    DOMAIN-SPECIFIC REPULSION:
        repulsion(v) now checks whether node v's domain is in the domain_set
        of any forbidden motif. Only forbidden motifs whose domain_set
        overlaps with v's neighborhood domain profile contribute to repulsion.

        This means: a physics/mathematics forbidden pattern repels high-degree
        nodes in physics/mathematics neighborhoods, but has zero effect on
        cognition/systems nodes. The field is spatially precise.

    DOMAIN SPIKE ACCUMULATION:
        domain_spike_weights[domain_set] = total spike_score for that boundary

        Explorer uses this to weight repulsion by historical spike severity
        at each specific domain boundary, not just total forbidden count.

═══════════════════════════════════════════════════════════════════════════════
"""


def _ensure_columns(conn):
    """
    Add domain_set and epoch_found columns to forbidden table if not present.
    Idempotent — safe to call every epoch.
    """
    c = conn.cursor()
    for col, typedef in [('domain_set', 'TEXT DEFAULT ""'),
                          ('epoch_found', 'INTEGER DEFAULT 0')]:
        try:
            c.execute(f"ALTER TABLE forbidden ADD COLUMN {col} {typedef}")
        except Exception:
            pass
    conn.commit()


def detect_forbidden(conn, compression, last_compression, epoch=0, threshold=0.15):
    """
    Watch for compression spikes and record forbidden motifs with domain context.

    When a spike exceeds threshold:
        1. Find the most prevalent motif at this moment
        2. Identify the domain composition of its participant nodes
        3. Record: signature, spike_score, domain_set, epoch_found

    Args:
        conn             : SQLite connection
        compression      : float — current epoch compression ratio
        last_compression : float — previous epoch compression ratio
        epoch            : int   — current epoch (recorded on forbidden motif)
        threshold        : float — spike detection threshold (default 0.15)

    Returns:
        (signature, spike) if spike detected, else (None, None)
    """
    _ensure_columns(conn)
    spike = compression - last_compression

    if spike <= threshold:
        return None, None

    c = conn.cursor()

    # Most prevalent motif — most likely contributor to the spike
    c.execute("SELECT signature, count FROM motifs ORDER BY count DESC LIMIT 1")
    row = c.fetchone()
    if not row:
        return None, None

    sig, count = row

    # ── Domain context: which domains were present when this motif fired? ─────
    # Approximate by looking at the domain distribution of recently active nodes
    # (the frontier — most likely participants in the spiking motif)
    c.execute("""
        SELECT DISTINCT n.domain
        FROM nodes n
        WHERE n.id IN (
            SELECT src FROM edges UNION SELECT dst FROM edges
        )
        ORDER BY n.id DESC
        LIMIT 30
    """)
    recent_domains = [row[0] for row in c.fetchall()]

    # Domain composition: count occurrences, take top 2 (the boundary)
    domain_counts = {}
    for d in recent_domains:
        domain_counts[d] = domain_counts.get(d, 0) + 1

    # The forbidden boundary is the two most represented domains at spike time
    top_domains  = sorted(domain_counts, key=domain_counts.get, reverse=True)[:2]
    domain_set   = ','.join(sorted(top_domains))

    # Record with domain context
    c.execute("""
        INSERT OR REPLACE INTO forbidden (signature, spike_score, domain_set, epoch_found)
        VALUES (?, ?, ?, ?)
    """, (sig, spike, domain_set, epoch))
    conn.commit()

    return sig, spike


def get_domain_spike_weights(conn):
    """
    Return accumulated spike weights per domain boundary.

    Returns dict: {domain_set_string: total_spike_score}

    Used by explorer.build_pressure_field() for spatially precise repulsion:
    only apply repulsion in the domain context where spikes have occurred.

    Example:
        {'mathematics,physics': 0.43, 'cognition,systems': 0.21}
    """
    _ensure_columns(conn)
    c = conn.cursor()
    c.execute("SELECT domain_set, spike_score FROM forbidden WHERE domain_set != ''")
    rows = c.fetchall()

    weights = {}
    for domain_set, spike in rows:
        weights[domain_set] = weights.get(domain_set, 0.0) + spike
    return weights


def get_forbidden_domain_sets(conn):
    """
    Return set of all domain_set strings that have forbidden motifs.
    Used by explorer for fast membership checks during field computation.
    """
    _ensure_columns(conn)
    c = conn.cursor()
    c.execute("SELECT DISTINCT domain_set FROM forbidden WHERE domain_set != ''")
    return set(row[0] for row in c.fetchall())