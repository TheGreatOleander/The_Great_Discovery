"""
hole_monitor.py — RETIRED (Phase 3)
The Great Discovery

This module was superseded before it was ever wired in.

The hole-watching logic it contained (aging registry, ripeness gating,
epoch tracking per hole) was a valid design but was never called from
driver.py. The driver instead calls hole_detector.find_nameable_holes()
directly each epoch, using the holes table and _asked_holes set in the
driver itself to prevent re-asking.

The useful concept from this module — holding a hole open until it has
accumulated sufficient age before questioning it — is handled differently
in the current architecture:

    - questioner._apply_pressure_boost() boosts the hole's endpoints
    - settler._is_held() checks the boost before filling
    - The hold releases naturally as boost decays at 0.15/epoch

If the aging/ripeness gating logic here is ever needed (e.g. for a
minimum-age filter on top of the current precision threshold), the
select_holes_to_question() function below can be adapted and wired into
driver.py's question generation block.

DO NOT import or call this module. It is retained for reference only.
"""


# ── Retained for reference ────────────────────────────────────────────────────

MIN_HOLE_AGE           = 3
MIN_PRECISION          = 0.15
MAX_QUESTIONS_PER_EPOCH = 2


def scan_open_holes(conn):
    """Find all transitive hole positions in the current graph."""
    c = conn.cursor()
    c.execute("SELECT src, dst FROM edges")
    edges    = c.fetchall()
    edge_set = set(edges)
    holes    = []
    for (a, b) in edges:
        for (b2, d) in edges:
            if b == b2 and a != d and (a, d) not in edge_set:
                holes.append((a, b, d))
    return holes


def update_hole_registry(registry, current_holes, epoch):
    """
    Update in-memory hole registry. Holes that persist accumulate age.
    Holes that disappear are removed.
    """
    current_positions = {}
    for (a, bridge, d) in current_holes:
        key = (a, d)
        if key not in current_positions:
            current_positions[key] = bridge

    to_remove = []
    for key in registry:
        if key in current_positions:
            registry[key]['age']       += 1
            registry[key]['last_seen']  = epoch
            registry[key]['bridge']     = current_positions[key]
        else:
            to_remove.append(key)
    for key in to_remove:
        del registry[key]

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
    """Select holes that are old enough and ripe for questioning."""
    candidates = [
        (key, info) for key, info in registry.items()
        if info['age'] >= MIN_HOLE_AGE and not info['questioned']
    ]
    candidates.sort(key=lambda x: x[1]['age'], reverse=True)
    return candidates[:max_questions]
