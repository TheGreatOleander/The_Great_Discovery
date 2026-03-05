"""
hole_monitor.py — Phase 3
The Great Discovery

Watches the topology for holes whose shapes have become precise enough to name.

Phase 2 detected holes and filled them. The questioner now runs before filling:
it reads the shape, asks the question, then the settler fills the hole.

But some holes should NOT be filled immediately. If a hole's shape is
precise enough and its surrounding structure is still actively changing,
the engine should hold the hole open — let it accumulate more constraints —
before settling it. A more constrained hole produces a more precise question.

The monitor:
  1. Scans the graph each epoch for candidate holes
  2. Tracks how long each hole position has been open
  3. When a hole reaches sufficient age AND precision, triggers the questioner
  4. Records named holes in the database — the engine's question log
  5. After questioning, passes the hole to the settler

The question log is the primary output of Phase 3.
It is the engine talking.
"""

import random
from questioner import interrogate_hole


# Minimum epochs a hole must persist before being questioned
# Too low: questions are vague (hole hasn't accumulated constraints)
# Too high: holes fill before they can be examined
MIN_HOLE_AGE  = 3

# Minimum precision score to generate a question
# (precision is computed by questioner from surrounding node count and relation variety)
MIN_PRECISION = 0.15

# Maximum holes to question per epoch (keep output readable)
MAX_QUESTIONS_PER_EPOCH = 2


def scan_open_holes(conn):
    """
    Find all transitive hole positions in the current graph.
    Returns list of (src, bridge, dst) triples where (src, dst) edge is missing.
    """
    c = conn.cursor()
    c.execute("SELECT src, dst FROM edges")
    edges = c.fetchall()
    edge_set = set(edges)

    holes = []
    for (a, b) in edges:
        for (b2, d) in edges:
            if b == b2 and a != d and (a, d) not in edge_set:
                holes.append((a, b, d))

    return holes


def update_hole_registry(registry, current_holes, epoch):
    """
    Update the in-memory hole registry.

    registry: dict mapping (src, dst) -> {bridge, first_seen, last_seen, age}
    current_holes: list of (src, bridge, dst) from current scan

    Holes that persist accumulate age. Holes that disappear are removed.
    """
    current_positions = {}
    for (a, bridge, d) in current_holes:
        key = (a, d)
        if key not in current_positions:
            current_positions[key] = bridge  # take first bridge found

    # Age existing holes
    to_remove = []
    for key in registry:
        if key in current_positions:
            registry[key]['age'] += 1
            registry[key]['last_seen'] = epoch
            registry[key]['bridge'] = current_positions[key]
        else:
            to_remove.append(key)

    for key in to_remove:
        del registry[key]

    # Register new holes
    for key, bridge in current_positions.items():
        if key not in registry:
            registry[key] = {
                'bridge':     bridge,
                'first_seen': epoch,
                'last_seen':  epoch,
                'age':        0,
                'questioned': False,
            }

    return registry


def select_holes_to_question(registry, max_questions=MAX_QUESTIONS_PER_EPOCH):
    """
    Select holes that are old enough and ripe for questioning.

    Prioritizes:
    - Holes that haven't been questioned yet
    - Holes with the most age (most constrained)
    - Up to max_questions per epoch
    """
    candidates = [
        (key, info) for key, info in registry.items()
        if info['age'] >= MIN_HOLE_AGE and not info['questioned']
    ]

    # Sort by age descending — most constrained first
    candidates.sort(key=lambda x: x[1]['age'], reverse=True)

    return candidates[:max_questions]


def record_question(conn, epoch, src_id, dst_id, question_record):
    """
    Persist a named hole question to the database.
    """
    c = conn.cursor()
    q = question_record

    c.execute("""
        INSERT INTO holes (epoch_found, shape_sig, demands, filled, filled_by)
        VALUES (?, ?, ?, 0, NULL)
    """, (
        epoch,
        f"hole:{src_id}->{dst_id}",
        q['question'],
    ))
    conn.commit()
    return c.lastrowid


def run_monitor(conn, epoch, registry, settler_fn):
    """
    Main monitor loop for one epoch.

    1. Scan current holes
    2. Update registry
    3. Question ripe holes
    4. Pass questioned holes to settler
    5. Return questions generated this epoch

    registry is mutated in place — pass the same dict across epochs.
    settler_fn: callable(conn, epoch, src_id, dst_id) -> settled record or None
    """
    current_holes = scan_open_holes(conn)
    update_hole_registry(registry, current_holes, epoch)

    to_question = select_holes_to_question(registry)
    questions_this_epoch = []

    for (src_id, dst_id), info in to_question:
        bridge_id = info['bridge']

        # Interrogate — get question and shape
        q_record = interrogate_hole(src_id, bridge_id, dst_id, conn)

        if q_record is None:
            continue

        if q_record['precision'] < MIN_PRECISION:
            continue

        # Mark as questioned so we don't ask again
        registry[(src_id, dst_id)]['questioned'] = True

        # Record in database
        record_question(conn, epoch, src_id, dst_id, q_record)

        # Now settle the hole
        settled = settler_fn(conn, epoch, src_id, dst_id)

        q_record['epoch']   = epoch
        q_record['settled'] = settled
        questions_this_epoch.append(q_record)

    return questions_this_epoch
