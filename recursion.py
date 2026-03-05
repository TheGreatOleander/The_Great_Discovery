"""
recursion.py — Phase 4 seed
The Great Discovery

═══════════════════════════════════════════════════════════════════════════════
RECURSIVE SHARPENING — THE ENGINE MAPS ITS OWN DISCOVERY PROCESS
═══════════════════════════════════════════════════════════════════════════════

Phase 3: the engine asks questions about the topology it is mapping.
Phase 4: the engine asks questions about its own act of asking questions.

The questions themselves become nodes. The structural patterns among questions
become motifs. The holes between question-nodes become meta-questions:
"What concept connects the thing I asked about at epoch 12 to the thing I
asked about at epoch 35?"

The act of discovery becomes part of the topology being discovered.
The map sharpens the mapmaker. The mapmaker sharpens the map.

─────────────────────────────────────────────────────────────────────────────
MECHANICS
─────────────────────────────────────────────────────────────────────────────

1. QUESTION NODES
   When the engine generates a question Q about hole H(src, dst):
       - Inject a new node into the graph: concept = question_token(Q),
         domain = 'recursion'
       - Connect it to src and dst with relation_type = 'emerges_from'
       - Connect it to the bridge node (if known) with 'requires'

   These are real graph nodes. They participate in motif sampling, pressure
   computation, and hole detection. The recursion layer is not a separate
   data structure — it is part of the same topology.

2. QUESTION-QUESTION EDGES
   After injecting a question node Q_new, scan existing question nodes
   Q_1..Q_n. If Q_new and Q_i share:
       - A domain boundary (same pair of domains)
       - A relation type in their profiles
   then connect them with 'analogous_to' (structural mirror relationship).

   These cross-question edges create a meta-topology over the question log.
   When the motif engine samples subgraphs containing question nodes, it
   begins to detect patterns in how the engine asks questions — which is
   Phase 4.

3. META-HOLES
   When two question nodes are connected but a third structurally-implied
   question node is missing (transitive closure in the question layer),
   that is a meta-hole: a question that the structure of asking questions
   implies but has not yet been asked.

   Meta-holes surface through the ordinary hole detection machinery —
   they are holes in the 'recursion' domain. The questioner will ask about
   them on the next cycle. These are the questions the mapmaker hasn't
   thought to ask yet, about the process of not yet having thought to ask.

4. RECURSION DEPTH LIMIT
   To prevent infinite regress, question nodes have a depth field:
       depth = 0 for object-level questions (about the domain graph)
       depth = 1 for meta-questions (about questions)
       depth = 2 for meta-meta-questions
   Maximum depth: MAX_RECURSION_DEPTH = 2

   This is not a philosophical limit. It is a practical one: at depth > 2,
   the meta-topology has not accumulated enough constraints to produce
   precise questions. The engine will raise this limit naturally as it
   matures.

─────────────────────────────────────────────────────────────────────────────
QUESTION TOKEN
─────────────────────────────────────────────────────────────────────────────
A question node's concept is a compact token encoding its structural profile:

    token = "{q_type}:{src_domain}:{dst_domain}:{dominant_relation}"

Examples:
    "bridge:physics:mathematics:emerges_from"
    "depth:cognition:cognition:requires"
    "boundary:systems:information:constrains"

This makes question nodes semantically legible to the motif engine.
Two question nodes with the same token are structurally equivalent questions
— they appear in the same position in their respective topologies.
When they cluster in motifs, that is the engine recognizing that it keeps
asking the same shape of question. That is signal.

═══════════════════════════════════════════════════════════════════════════════
"""

import random
from semantics import relation_weight

MAX_RECURSION_DEPTH = 2
RECURSION_DOMAIN    = 'recursion'


# ── Question token ────────────────────────────────────────────────────────────

def question_token(q_record):
    """
    Compact structural token for a question — used as node concept.

    Format: "{type}:{src_domain}:{dst_domain}:{relation}"

    Two questions with the same token asked the same structural question
    in different parts of the topology.
    """
    return (
        f"{q_record.get('type', 'unknown')}"
        f":{q_record.get('src_domain', 'unknown')}"
        f":{q_record.get('dst_domain', 'unknown')}"
        f":{q_record.get('relation', 'related')}"
    )


# ── Question node injection ────────────────────────────────────────────────────

def inject_question_node(conn, epoch, q_record, depth=0):
    """
    Inject a question as a real graph node.

    Creates a node with:
        concept  = question_token(q_record)
        domain   = 'recursion'
        depth    = recursion depth (0 = object-level)

    Connects it to:
        src node → new node  via 'emerges_from'  (question emerges from src)
        new node → dst node  via 'requires'       (question demands dst)

    Returns the new node's ID, or None if depth limit exceeded.
    """
    if depth > MAX_RECURSION_DEPTH:
        return None

    c = conn.cursor()

    # Ensure depth column exists (idempotent)
    try:
        c.execute("ALTER TABLE nodes ADD COLUMN depth INTEGER DEFAULT 0")
        conn.commit()
    except Exception:
        pass

    token   = question_token(q_record)
    src_id  = q_record.get('src_id')
    dst_id  = q_record.get('dst_id')

    # Insert question node
    c.execute(
        "INSERT INTO nodes (concept, domain, introduced, depth) VALUES (?, ?, ?, ?)",
        (token, RECURSION_DOMAIN, epoch, depth)
    )
    q_node_id = c.lastrowid

    # Connect to the hole's endpoints
    if src_id is not None:
        c.execute(
            "INSERT INTO edges VALUES (?, ?, ?, ?)",
            (src_id, q_node_id, 'emerges_from', relation_weight('emerges_from'))
        )
    if dst_id is not None:
        c.execute(
            "INSERT INTO edges VALUES (?, ?, ?, ?)",
            (q_node_id, dst_id, 'requires', relation_weight('requires'))
        )

    conn.commit()
    return q_node_id


def link_question_nodes(conn, new_q_node_id, new_q_record):
    """
    Connect the new question node to existing question nodes.

    Two kinds of connection:

    1. ANALOGOUS_TO (undirected mirror) — same type AND (same relation OR same boundary).
       These are structurally parallel questions.

    2. CAUSES (directional chain) — new question's dst_domain matches an existing
       question's src_domain. This creates a transitive path through the question
       layer: Q_a → Q_b → Q_c, enabling meta-hole detection via find_meta_holes().

    Both are needed. Analogous_to creates clusters. Causes creates chains.
    Chains are what produce meta-holes (missing transitive closures).
    """
    c = conn.cursor()

    new_token = question_token(new_q_record)
    new_parts = new_token.split(':')
    if len(new_parts) < 4:
        return

    new_type, new_src_dom, new_dst_dom, new_rel = new_parts

    c.execute(
        "SELECT id, concept FROM nodes WHERE domain = ? AND id != ?",
        (RECURSION_DOMAIN, new_q_node_id)
    )
    existing_q_nodes = c.fetchall()

    c.execute("SELECT src, dst FROM edges")
    edge_set = set(c.fetchall())

    for (existing_id, existing_token) in existing_q_nodes:
        parts = existing_token.split(':')
        if len(parts) < 4:
            continue
        ex_type, ex_src_dom, ex_dst_dom, ex_rel = parts

        same_boundary = {new_src_dom, new_dst_dom} == {ex_src_dom, ex_dst_dom}
        same_relation = new_rel == ex_rel
        same_type     = new_type == ex_type

        # Analogous mirror
        if (same_boundary or same_relation) and same_type:
            if (new_q_node_id, existing_id) not in edge_set:
                c.execute(
                    "INSERT INTO edges VALUES (?, ?, ?, ?)",
                    (new_q_node_id, existing_id,
                     'analogous_to', relation_weight('analogous_to'))
                )
                edge_set.add((new_q_node_id, existing_id))

        # Directional chain: new question's dst_domain feeds into existing question's src_domain
        # new: A→B  existing: B→C  ⟹  new → existing (causes)
        if new_dst_dom == ex_src_dom and new_q_node_id != existing_id:
            if (new_q_node_id, existing_id) not in edge_set:
                c.execute(
                    "INSERT INTO edges VALUES (?, ?, ?, ?)",
                    (new_q_node_id, existing_id,
                     'causes', relation_weight('causes'))
                )
                edge_set.add((new_q_node_id, existing_id))

        # Reverse chain: existing question's dst_domain feeds into new question's src_domain
        # existing: A→B  new: B→C  ⟹  existing → new (causes)
        if ex_dst_dom == new_src_dom and existing_id != new_q_node_id:
            if (existing_id, new_q_node_id) not in edge_set:
                c.execute(
                    "INSERT INTO edges VALUES (?, ?, ?, ?)",
                    (existing_id, new_q_node_id,
                     'causes', relation_weight('causes'))
                )
                edge_set.add((existing_id, new_q_node_id))

    conn.commit()


# ── Meta-hole detection ───────────────────────────────────────────────────────

def find_meta_holes(conn):
    """
    Find holes in the question layer — meta-questions implied by the
    structure of existing question nodes.

    A meta-hole exists when:
        - Question node A connects to question node B
        - Question node B connects to question node C
        - No edge exists A → C
        - A, B, C are all in the 'recursion' domain

    These are the questions that the pattern of asking questions implies
    but hasn't yet asked.

    Returns list of (src_q_id, dst_q_id) meta-hole positions.
    """
    c = conn.cursor()

    c.execute("SELECT id FROM nodes WHERE domain = ?", (RECURSION_DOMAIN,))
    q_node_ids = set(row[0] for row in c.fetchall())

    if len(q_node_ids) < 3:
        return []

    c.execute("SELECT src, dst FROM edges")
    all_edges = c.fetchall()
    edge_set  = set(all_edges)

    # Only edges between question nodes
    q_edges = [(a, b) for (a, b) in all_edges
               if a in q_node_ids and b in q_node_ids]

    meta_holes = []
    seen       = set()

    for (a, b) in q_edges:
        for (b2, d) in q_edges:
            if b == b2 and a != d and (a, d) not in edge_set:
                key = (min(a, d), max(a, d))
                if key not in seen:
                    seen.add(key)
                    meta_holes.append((a, d))

    return meta_holes


# ── Main recursion step ───────────────────────────────────────────────────────

def run_recursion_step(conn, epoch, questions):
    """
    Execute one recursion step for all questions generated this epoch.

    For each question:
        1. Inject as a graph node (depth=0 for object-level questions)
        2. Link to structurally similar question nodes
        3. Return meta-holes for the driver to report

    The driver passes the returned meta-holes to the questioner on the
    next cycle if they meet the precision threshold. This is Phase 4.

    Args:
        conn      : SQLite connection
        epoch     : int — current epoch
        questions : list of question records from generate_questions()

    Returns:
        meta_holes : list of (src_q_id, dst_q_id) — implied meta-questions
        q_node_ids : list of new question node IDs injected this epoch
    """
    q_node_ids = []

    for q in questions:
        q_node_id = inject_question_node(conn, epoch, q, depth=0)
        if q_node_id is not None:
            link_question_nodes(conn, q_node_id, q)
            q['q_node_id'] = q_node_id
            q_node_ids.append(q_node_id)

    meta_holes = find_meta_holes(conn)

    return meta_holes, q_node_ids