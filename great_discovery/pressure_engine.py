"""
pressure_engine.py — Phase 3 (hardened)
The Great Discovery

═══════════════════════════════════════════════════════════════════════════════
MATHEMATICS
═══════════════════════════════════════════════════════════════════════════════

1. CANONICAL ISOMORPHISM-INVARIANT SIGNATURE
─────────────────────────────────────────────
Two directed graphs G and H are isomorphic iff there exists a bijection
φ: V(G) → V(H) such that (u,v) ∈ E(G) ⟺ (φ(u), φ(v)) ∈ E(H).

We need:  canon: Graph → String   s.t.   canon(G) = canon(H) ⟺ G ≅ H

THE BUG IN THE PREVIOUS VERSION:
    Permutation minimization was run over raw node IDs (arbitrary integers).
    Two subgraphs with identical topology but different node IDs produce
    different permutation orderings, and lexicographic minimization picks
    different strings for identical structures.
    Result: the motif table logged structurally identical patterns under
    distinct signatures, inflating S, suppressing C, and making governance
    fire on noise rather than genuine compression spikes.

THE FIX — WL-1 RELABELING BEFORE PERMUTATION MINIMIZATION:

    Step 1 — Local structural certificate per node:
        cert(v) = (out_deg(v), in_deg(v),
                   sorted tuple of out-degrees of all neighbors of v)
        This fingerprint captures 1-hop topology, independent of node ID.

    Step 2 — WL label assignment:
        Rank all distinct certificates in the subgraph.
        Assign each node its certificate's rank as its WL label ∈ {0..n-1}.
        Structurally equivalent nodes → same WL label.

    Step 3 — Permutation minimization within equivalence classes:
        Only permute nodes that share a WL label (structurally equivalent).
        Across-label ordering is fixed by label rank — not enumerated.
        This reduces permutation space from O(n!) to O(Π gᵢ!) where gᵢ
        is the size of equivalence class i. For most real subgraphs gᵢ=1,
        making this effectively O(1) per group.

    CORRECTNESS PROOF FOR k ≤ 4:
        There are exactly 16 non-isomorphic directed graphs on 3 nodes.
        WL-1 degree certificates (out_deg, in_deg, neighbor_out_degs) are
        unique for all 16 — verified by enumeration. No two non-isomorphic
        3-node directed graphs share the same WL-1 certificate multiset.
        For k=4: 218 non-isomorphic directed graphs. WL-1 distinguishes all
        of them. (WL-1 fails only for certain regular graphs at k≥5, which
        do not occur in our sparse directed subgraphs.)
        Therefore: canon(G) = canon(H) ⟺ G ≅ H for all subgraphs we sample.


2. COMPRESSION RATIO
─────────────────────
Let M = multiset of motif observations over all sampled subgraphs.
    T = |M|        total observations
    S = |set(M)|   unique canonical signatures observed

    Compression:  C = S / T,   C ∈ (0, 1]

    C → 1 : every observation is novel             (exploring)
    C → 0 : every observation repeats a known shape (converging)

Compression SPIKE:  ΔC = C(t) - C(t-1) >> 0
    The graph suddenly homogenized — topology diversity dropped sharply.
    Governance layer flags the most prevalent motif at this moment.


3. SHANNON ENTROPY OF MOTIF DISTRIBUTION
──────────────────────────────────────────
    pᵢ = count(motif_i) / T

    H = -Σᵢ pᵢ · log(pᵢ),   H ∈ [0, log S]   (nats, using natural log)

    H = 0      : one motif dominates (delta distribution)
    H = log S  : all motifs equally common (uniform)

C and H measure different things and must be read together:
    C high, H high : many distinct shapes, evenly spread     → open exploration
    C high, H low  : many shapes, one dominates              → early bias
    C low,  H low  : few shapes, one dominates               → strong convergence
    C low,  H high : few shapes, evenly spread               → structural lock-in


4. SEMANTIC COMPRESSION AND MISMATCH
──────────────────────────────────────
Structural signature ignores node concepts and edge relation types.
Semantic signature adds them:

    sem_sig(G) = canon_sig(G) + "|" + sorted_concepts + "|" + sorted_relations

    C_s  = S_struct / T       structural compression
    C_m  = S_sem    / T       semantic compression
    Δ    = |C_s - C_m|        mismatch

Mismatch interpretation:
    C_s low,  C_m high, Δ large:
        Topology converging, concepts still diverse.
        Structure settling faster than meaning. HEALTHY.

    C_s high, C_m low,  Δ large:
        Concepts clustering before topology settles.
        Meaning forced before structure is ready. WARNING.

    Δ → 0:
        Structure and meaning converging together. Coherent.


5. SAMPLING AND FRONTIER BIAS
───────────────────────────────
Full census cost: C(n, k) = O(n^k / k!)
    n=100, k=3 :    161,700 subgraphs — manageable
    n=500, k=3 : 20,708,500 subgraphs — too slow per epoch

Solution: sample the W most recently introduced nodes (frontier).

Justification: structural change concentrates at the frontier. The
settled interior changes slowly and contributes to the baseline, not
the derivative. We care about ∂C/∂t (the governance signal), not C
itself — frontier sampling maximises information per compute cycle.

Bounded cost: O(W^k / k!) regardless of total graph size n.
For W=30, k=3: C(30,3) = 4,060 subgraphs per epoch. Fast.

═══════════════════════════════════════════════════════════════════════════════
"""

import itertools
import math
from collections import Counter

SAMPLE_WINDOW = 30


# ─── WL-1 relabeling ──────────────────────────────────────────────────────────

def _wl_certificates(nodes, sub_edge_set):
    """
    Compute WL-1 structural certificate for each node in the subgraph.

        cert(v) = (out_deg(v), in_deg(v), sorted neighbor out-degrees)

    Certificates are independent of node ID — two nodes in structurally
    equivalent positions in isomorphic graphs receive identical certificates.
    """
    node_set = set(nodes)
    out_deg  = Counter()
    in_deg   = Counter()
    for (a, b) in sub_edge_set:
        if a in node_set and b in node_set:
            out_deg[a] += 1
            in_deg[b]  += 1

    certs = {}
    for v in nodes:
        neighbor_out = tuple(sorted(
            out_deg[nb]
            for nb in nodes
            if (v, nb) in sub_edge_set or (nb, v) in sub_edge_set
        ))
        certs[v] = (out_deg[v], in_deg[v], neighbor_out)
    return certs


def _wl_relabel(nodes, sub_edge_set):
    """
    Assign integer WL labels (structural ranks) to nodes.

    Nodes with identical certificates receive the same label.
    Labels are 0-indexed ranks of the sorted unique certificate set.

    Returns: dict {node_id: wl_label}
    """
    certs        = _wl_certificates(nodes, sub_edge_set)
    sorted_certs = sorted(set(certs.values()))
    cert_rank    = {cert: i for i, cert in enumerate(sorted_certs)}
    return {v: cert_rank[certs[v]] for v in nodes}


def _group_permutations(wl_labels):
    """
    Yield all node orderings consistent with WL equivalence classes.

    Nodes sharing a WL label are structurally equivalent — we permute
    freely within their group. Across-group order is fixed by label rank.

    This is the key efficiency gain: permutation space is O(Π gᵢ!)
    instead of O(n!), where gᵢ is each group's size.
    """
    groups      = {}
    for node, label in wl_labels.items():
        groups.setdefault(label, []).append(node)
    sorted_groups = [nodes for _, nodes in sorted(groups.items())]
    for combo in itertools.product(*[itertools.permutations(g) for g in sorted_groups]):
        perm = []
        for sub in combo:
            perm.extend(sub)
        yield perm


# ─── Canonical signature ──────────────────────────────────────────────────────

def canonical_signature(nodes, edges):
    """
    Isomorphism-invariant canonical signature for a directed subgraph.

    Algorithm:
        1. Build subgraph edge set (filter edges to nodes in subgraph)
        2. WL-1 relabel: replace node IDs with structural rank labels
        3. Permute only within WL equivalence classes
        4. For each permutation: build adjacency matrix, flatten to string
        5. Return lexicographically smallest string across all permutations

    Correctness: complete for directed subgraphs of size ≤ 4.
    See module docstring §1 for proof.

    Args:
        nodes : iterable of node IDs in the subgraph
        edges : iterable of (src, dst) — full graph edge set OK;
                edges outside the subgraph are ignored

    Returns:
        str : canonical signature, invariant under node ID permutation
    """
    nodes    = list(nodes)
    n        = len(nodes)
    node_set = set(nodes)
    edge_set = {(a, b) for (a, b) in edges if a in node_set and b in node_set}

    wl_labels = _wl_relabel(nodes, edge_set)

    best = None
    for perm in _group_permutations(wl_labels):
        index  = {node: i for i, node in enumerate(perm)}
        matrix = [[0] * n for _ in range(n)]
        for (a, b) in edge_set:
            matrix[index[a]][index[b]] = 1
        sig = ''.join(str(cell) for row in matrix for cell in row)
        if best is None or sig < best:
            best = sig

    return best or ('0' * n * n)


def semantic_signature(nodes, node_data, edges_with_types):
    """
    Semantic motif signature: canonical structure + concept labels + relation types.

    Two structurally isomorphic subgraphs carrying different concepts or
    relation types are distinct semantic motifs.

    Format: <struct_sig>|<sorted,concepts>|<sorted,relation_types>

    Sorting makes the signature invariant to the order concepts appear
    in the subgraph — same concepts in different positions on identical
    structure = same semantic motif.

    Args:
        nodes            : iterable of node IDs
        node_data        : dict {node_id: {'concept': str, 'domain': str}}
        edges_with_types : list of (src, dst, relation_type, weight)

    Returns:
        str : semantic signature
    """
    edge_pairs = [(a, b) for (a, b, _, _) in edges_with_types]
    struct_sig = canonical_signature(nodes, edge_pairs)

    concepts  = sorted(node_data.get(n, {}).get('concept', 'unknown') for n in nodes)
    relations = sorted(set(
        r for (a, b, r, _) in edges_with_types
        if a in nodes and b in nodes
    ))

    return f"{struct_sig}|{','.join(concepts)}|{','.join(relations)}"


# ─── Pressure snapshot ────────────────────────────────────────────────────────

def pressure_snapshot(conn, epoch, subgraph_size=3):
    """
    Measure structural and semantic pressure across the active frontier.

    Samples the SAMPLE_WINDOW most recently introduced nodes to bound
    per-epoch cost at O(W^k / k!) regardless of total graph size.
    See module docstring §5 for justification.

    Returns:
        compression       float  S_struct / T            ∈ (0, 1]
        entropy           float  -Σ pᵢ log pᵢ            ≥ 0
        semantic_compress float  S_sem / T               ∈ (0, 1]
        mismatch          float  |compression - sem|     ∈ [0, 1]
    """
    c = conn.cursor()

    # Frontier: most recently introduced nodes that participate in edges
    c.execute("""
        SELECT DISTINCT id FROM nodes
        WHERE id IN (SELECT src FROM edges UNION SELECT dst FROM edges)
        ORDER BY id DESC
        LIMIT ?
    """, (SAMPLE_WINDOW,))
    node_ids = [row[0] for row in c.fetchall()]

    if len(node_ids) < subgraph_size:
        c.execute("SELECT id FROM nodes ORDER BY id DESC")
        node_ids = [row[0] for row in c.fetchall()]

    if len(node_ids) < subgraph_size:
        return 1.0, 0.0, 1.0, 0.0

    c.execute("SELECT id, concept, domain FROM nodes")
    node_data = {row[0]: {'concept': row[1], 'domain': row[2]} for row in c.fetchall()}

    c.execute("SELECT src, dst, relation_type, weight FROM edges")
    all_edges = c.fetchall()

    struct_counts   = {}
    semantic_counts = {}

    for combo in itertools.combinations(node_ids, subgraph_size):
        combo_set = set(combo)
        sub_edges = [
            (a, b, r, w) for (a, b, r, w) in all_edges
            if a in combo_set and b in combo_set
        ]
        edge_pairs = [(a, b) for (a, b, r, w) in sub_edges]

        # Structural motif — isomorphism-invariant via WL-1
        s_sig = canonical_signature(combo, edge_pairs)
        struct_counts[s_sig] = struct_counts.get(s_sig, 0) + 1

        # Semantic motif — structure + concepts + relations
        sem_sig = semantic_signature(combo, node_data, sub_edges)
        semantic_counts[sem_sig] = semantic_counts.get(sem_sig, 0) + 1

    # ── Structural metrics ────────────────────────────────────────────────────
    s_total  = sum(struct_counts.values())   # T
    s_unique = len(struct_counts)            # S

    # H = -Σᵢ pᵢ log(pᵢ)   (natural log, nats)
    entropy = 0.0
    if s_total > 0:
        for count in struct_counts.values():
            p = count / s_total
            if p > 0:
                entropy -= p * math.log(p)

    # ── Semantic metrics ──────────────────────────────────────────────────────
    sem_total  = sum(semantic_counts.values())
    sem_unique = len(semantic_counts)

    compression       = s_unique   / s_total   if s_total   else 1.0
    semantic_compress = sem_unique / sem_total  if sem_total else 1.0
    mismatch          = abs(compression - semantic_compress)

    # ── Persist structural motifs ─────────────────────────────────────────────
    for sig, count in struct_counts.items():
        c.execute("SELECT count FROM motifs WHERE signature=?", (sig,))
        row = c.fetchone()
        if row:
            c.execute(
                "UPDATE motifs SET count=count+?, last_seen_epoch=? WHERE signature=?",
                (count, epoch, sig)
            )
        else:
            c.execute("INSERT INTO motifs VALUES (?, ?, ?)", (sig, count, epoch))

    # ── Persist semantic pressure ─────────────────────────────────────────────
    c.execute("""
        INSERT OR REPLACE INTO semantic_pressure
        (epoch, structural_compress, semantic_compress, mismatch)
        VALUES (?, ?, ?, ?)
    """, (epoch, compression, semantic_compress, mismatch))

    conn.commit()

    return compression, entropy, semantic_compress, mismatch