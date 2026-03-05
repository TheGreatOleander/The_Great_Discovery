"""
questioner.py — Phase 3 (hardened)
The Great Discovery

═══════════════════════════════════════════════════════════════════════════════
QUESTION FEEDBACK LOOP
═══════════════════════════════════════════════════════════════════════════════

Previously: questions were generated, logged, and forgotten. Nothing about
asking a question changed how the engine explored. The map asked something
and then immediately moved on as if it hadn't asked.

Now: when a question is generated for a hole at (src, dst), the precision
of that hole's structural profile is written back to the nodes table as a
pressure_boost field. The exploration pressure field reads this boost,
increasing the pull toward the hole's neighborhood on subsequent epochs.

Effect: the engine circles back. After asking a question, it explores more
aggressively in that region — accumulating more constraints, producing
better-shaped questions on the next cycle, and eventually either settling
the hole with higher confidence or discovering that the hole resists settling
(which is itself structural signal).

PRESSURE BOOST MECHANICS:
    boost(v) = precision * QUESTION_PRESSURE_SCALE
    Applied to src and dst nodes of the questioned hole.
    Decays by BOOST_DECAY_RATE each epoch (handled in driver).
    Minimum value: 0.0

    QUESTION_PRESSURE_SCALE = 1.2  (questions carry more weight than
                                    ordinary structural void tension)
    BOOST_DECAY_RATE        = 0.15 per epoch

═══════════════════════════════════════════════════════════════════════════════
"""

import random
from collections import Counter

RELATION_IMPLIES = {
    'causes':        ('is caused by', 'produces', 'drives'),
    'requires':      ('enables', 'underlies', 'is prerequisite for'),
    'constrains':    ('is bounded by', 'shapes', 'limits'),
    'amplifies':     ('is strengthened by', 'resonates with', 'scales with'),
    'stabilizes':    ('grounds', 'regulates', 'dampens'),
    'emerges_from':  ('gives rise to', 'generates', 'produces higher-order structure in'),
    'destabilizes':  ('disrupts', 'perturbs', 'breaks symmetry in'),
    'analogous_to':  ('mirrors', 'structurally resembles', 'maps onto'),
    'is_dual_of':    ('is the complement of', 'inverts', 'is the other face of'),
    'related':       ('connects to', 'associates with', 'links'),
}

DEMAND_TEMPLATES = {
    ('causes','requires'):        "something that is both an effect and a prerequisite",
    ('requires','emerges_from'):  "something that must exist before a higher-order property can arise",
    ('constrains','amplifies'):   "something that is both limited and strengthened simultaneously",
    ('stabilizes','causes'):      "something that grounds a process while initiating another",
    ('analogous_to','causes'):    "a structural mirror that also drives an outcome",
    ('emerges_from','constrains'):"something that arises from below and limits from above",
    ('is_dual_of','requires'):    "a complementary concept that is also a dependency",
}

QUESTION_PRESSURE_SCALE = 1.2
BOOST_DECAY_RATE        = 0.15


def _pick(opts):
    return random.choice(opts) if opts else 'connects to'

def _dom(items):
    if not items:
        return None
    c = Counter(items)
    return c.most_common(1)[0][0]


def compose_question(profile):
    """
    Compose a natural language question from a hole's structural profile.
    Three types: BRIDGE (cross-domain), DEPTH (within-domain), BOUNDARY (forbidden-adjacent).
    """
    src  = profile['src_concept'];  dst  = profile['dst_concept']
    sdom = profile['src_domain'];   ddom = profile['dst_domain']
    rel  = profile['dominant_relation']
    adj  = profile['adjacent_concepts']
    top  = profile['top_relations']
    inb  = profile['inbound_relations']
    outb = profile['outbound_relations']
    forb = profile['forbidden_adjacent']
    ndom = profile['n_domains']
    prec = profile['precision']

    if forb and ndom >= 2:
        q_type = 'boundary'
    elif profile['is_cross_domain']:
        q_type = 'bridge'
    else:
        q_type = 'depth'

    rel_phrase = _pick(RELATION_IMPLIES.get(rel, ('connects to',)))

    if q_type == 'bridge':
        in_r      = _dom(inb)  or rel
        out_r     = _dom(outb) or rel
        demand    = DEMAND_TEMPLATES.get(tuple(sorted([in_r, out_r])), None) \
                 or DEMAND_TEMPLATES.get((in_r, out_r), None)
        out_phrase = _pick(RELATION_IMPLIES.get(out_r, ('connects to',)))
        if demand and adj:
            question = (
                f"What concept bridges {sdom} and {ddom} — {demand} — "
                f"such that '{src}' {rel_phrase} it, and it {out_phrase} '{dst}'?"
            )
        elif adj:
            question = (
                f"What lies between {sdom} and {ddom} where '{src}' {rel_phrase} "
                f"something that in turn {out_phrase} '{dst}'? "
                f"The surrounding structure includes '{adj[0]}' — "
                f"what does the gap between them demand?"
            )
        else:
            question = (
                f"What concept does {sdom} share with {ddom} "
                f"that '{src}' {rel_phrase} and '{dst}' depends on?"
            )

    elif q_type == 'depth':
        sec_rel    = top[1] if len(top) > 1 else rel
        sec_phrase = _pick(RELATION_IMPLIES.get(sec_rel, ('connects to',)))
        if adj and len(adj) >= 2:
            question = (
                f"Within {sdom}: what does '{src}' {rel_phrase} "
                f"that also {sec_phrase} '{dst}', "
                f"given that '{adj[0]}' already occupies the adjacent position? "
                f"The structure is asking for something more specific."
            )
        else:
            question = (
                f"Within {sdom}: what concept sits between '{src}' and '{dst}' "
                f"such that '{src}' {rel_phrase} it "
                f"and it is required for '{dst}' to function?"
            )

    else:  # boundary
        border = ' and '.join(profile['border_domains'])
        if adj:
            question = (
                f"At the boundary of {border}: "
                f"what must exist between '{src}' and '{dst}' "
                f"that {rel_phrase} the surrounding structure, "
                f"given that configurations similar to '{adj[0]}' have been ruled out? "
                f"The forbidden patterns have shaped this gap. What fits the shape they left?"
            )
        else:
            question = (
                f"At the edge where {sdom} meets {ddom}: "
                f"what concept is required between '{src}' and '{dst}' "
                f"that the surrounding forbidden structure cannot be? "
                f"The table has edges here. What do they frame?"
            )

    return {
        'question':     question,
        'type':         q_type,
        'precision':    prec,
        'domains':      profile['border_domains'],
        'key_concepts': [src, dst],
        'relation':     rel,
        'src_domain':   sdom,
        'dst_domain':   ddom,
        'src_id':       profile['src_id'],
        'dst_id':       profile['dst_id'],
    }


def _apply_pressure_boost(conn, src_id, dst_id, precision):
    """
    Write a pressure boost back to the nodes involved in this question.

    The boost increases pull(v) in build_pressure_field() on subsequent epochs,
    causing the engine to explore more aggressively near this hole before settling.

    The nodes table gains a `pressure_boost` column (added on first use via
    ALTER TABLE — safe to call multiple times, silently ignores if column exists).
    """
    c = conn.cursor()

    # Add column if not present (idempotent)
    try:
        c.execute("ALTER TABLE nodes ADD COLUMN pressure_boost REAL DEFAULT 0.0")
        conn.commit()
    except Exception:
        pass  # Column already exists

    boost = precision * QUESTION_PRESSURE_SCALE
    c.execute(
        "UPDATE nodes SET pressure_boost = MIN(pressure_boost + ?, 3.0) WHERE id IN (?, ?)",
        (boost, src_id, dst_id)
    )
    conn.commit()


def decay_pressure_boosts(conn):
    """
    Decay all pressure boosts by BOOST_DECAY_RATE each epoch.
    Called once per epoch from the driver after exploration.

    boost(t+1) = max(0, boost(t) - BOOST_DECAY_RATE)

    This ensures questions have a lasting but finite influence on exploration.
    A precision=1.0 question produces a boost of 1.2, which decays to zero
    in ~8 epochs — long enough to accumulate more constraints around the hole.
    """
    c = conn.cursor()
    try:
        c.execute("""
            UPDATE nodes
            SET pressure_boost = MAX(0.0, pressure_boost - ?)
            WHERE pressure_boost > 0
        """, (BOOST_DECAY_RATE,))
        conn.commit()
    except Exception:
        pass  # Column may not exist yet on first epochs


def generate_questions(conn, epoch, profiles):
    """
    Generate questions from hole profiles and apply pressure feedback.

    For each profile:
        1. Compose the question
        2. Log to holes table
        3. Apply pressure boost to src/dst nodes (feedback loop)

    Returns list of question records.
    """
    if not profiles:
        return []

    c = conn.cursor()
    questions = []

    for profile in profiles:
        q = compose_question(profile)

        # Log to holes table
        c.execute(
            "INSERT INTO holes (epoch_found, shape_sig, demands, filled, filled_by) VALUES (?,?,?,0,NULL)",
            (epoch, f"{profile['src_id']}-{profile['dst_id']}", q['question'])
        )
        q['hole_id'] = c.lastrowid

        # Feedback: boost pressure on the nodes this question is about
        _apply_pressure_boost(conn, profile['src_id'], profile['dst_id'], profile['precision'])

        questions.append(q)

    conn.commit()
    return questions


def interrogate_hole(src_id, bridge_id, dst_id, conn):
    """
    Legacy interface for hole_monitor.py.
    Constructs a minimal profile from node data and returns a question record.
    """
    from hole_detector import analyze_hole
    profile = analyze_hole(conn, src_id, dst_id)
    if profile is None:
        return None
    return compose_question(profile)


# ─── Meta-question composition ────────────────────────────────────────────────

def compose_meta_question(src_q_node, dst_q_node, conn):
    """
    Compose a question about a hole between two question nodes.

    This is a meta-question: not about the domain topology, but about
    the structure of the questions themselves. It asks what conceptual
    relationship connects two questions that the topology implies should
    be connected but aren't yet.

    src_q_node, dst_q_node: dicts with {id, concept, domain}
    concept format: "{type}:{src_domain}:{dst_domain}:{relation}"

    A meta-question has type='meta' and domain='recursion'.
    """
    def parse_token(token):
        parts = token.split(':')
        if len(parts) >= 4:
            return {'type': parts[0], 'src_domain': parts[1],
                    'dst_domain': parts[2], 'relation': parts[3]}
        return {'type': 'unknown', 'src_domain': 'unknown',
                'dst_domain': 'unknown', 'relation': 'related'}

    src_tok = parse_token(src_q_node.get('concept', ''))
    dst_tok = parse_token(dst_q_node.get('concept', ''))

    # What structural relationship connects these two questions?
    src_boundary = f"{src_tok['src_domain']}/{src_tok['dst_domain']}"
    dst_boundary = f"{dst_tok['src_domain']}/{dst_tok['dst_domain']}"

    same_type     = src_tok['type']     == dst_tok['type']
    same_relation = src_tok['relation'] == dst_tok['relation']
    shared_domain = len({src_tok['src_domain'], src_tok['dst_domain']} &
                        {dst_tok['src_domain'], dst_tok['dst_domain']}) > 0

    if same_type and same_relation:
        question = (
            f"Both '{src_boundary}' and '{dst_boundary}' produce "
            f"{src_tok['type']} questions about '{src_tok['relation']}' relationships. "
            f"What structural principle makes the same question shape appear "
            f"at both boundaries? What does this recurrence demand?"
        )
    elif same_type and shared_domain:
        shared = list({src_tok['src_domain'], src_tok['dst_domain']} &
                      {dst_tok['src_domain'], dst_tok['dst_domain']})[0]
        question = (
            f"Two {src_tok['type']} questions both touch '{shared}' — "
            f"one from the {src_boundary} boundary, one from {dst_boundary}. "
            f"What is it about '{shared}' that makes it a recurring site "
            f"for this type of structural gap?"
        )
    else:
        question = (
            f"The engine has asked about the gap at '{src_boundary}' "
            f"({src_tok['type']}, {src_tok['relation']}) "
            f"and the gap at '{dst_boundary}' "
            f"({dst_tok['type']}, {dst_tok['relation']}). "
            f"What structural relationship between these two gaps "
            f"does the topology imply but has not yet named?"
        )

    return {
        'question':     question,
        'type':         'meta',
        'precision':    0.6,   # Meta-questions start with lower precision
        'domains':      ['recursion'],
        'key_concepts': [src_q_node.get('concept', '?'),
                         dst_q_node.get('concept', '?')],
        'relation':     'analogous_to',
        'src_domain':   'recursion',
        'dst_domain':   'recursion',
        'src_id':       src_q_node.get('id'),
        'dst_id':       dst_q_node.get('id'),
        'is_meta':      True,
    }


def generate_meta_questions(conn, epoch, meta_holes):
    """
    Generate meta-questions for holes detected in the question layer.

    meta_holes: list of (src_q_id, dst_q_id) from recursion.find_meta_holes()

    Returns list of meta-question records (same structure as regular questions,
    with type='meta' and is_meta=True).
    """
    if not meta_holes:
        return []

    c = conn.cursor()
    c.execute("SELECT id, concept, domain FROM nodes WHERE domain = 'recursion'")
    q_nodes = {row[0]: {'id': row[0], 'concept': row[1], 'domain': row[2]}
               for row in c.fetchall()}

    meta_questions = []
    for (src_id, dst_id) in meta_holes[:2]:   # max 2 per epoch
        if src_id not in q_nodes or dst_id not in q_nodes:
            continue
        mq = compose_meta_question(q_nodes[src_id], q_nodes[dst_id], conn)

        # Log to holes table
        c.execute(
            "INSERT INTO holes (epoch_found, shape_sig, demands, filled, filled_by) VALUES (?,?,?,0,NULL)",
            (epoch, f"meta:{src_id}-{dst_id}", mq['question'])
        )
        mq['hole_id'] = c.lastrowid
        meta_questions.append(mq)

    conn.commit()
    return meta_questions