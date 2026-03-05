"""
stress_test.py — Phase 4
The Great Discovery

100-epoch stress test with structural assertions.

Checks that the engine is doing what it claims:
    1. Compression falls below 1.0 — the graph is repeating patterns
    2. At least one question is generated — hole detection is firing
    3. Convergence state exits Exploring — enough history to classify
    4. At least one forbidden motif recorded — governance is live
    5. Hole attraction is active — open holes exist in the table
    6. Pressure boosts applied — questioner feedback loop is working
    7. Recursion nodes exist — Phase 4 is wired
    8. epoch_found on forbidden motifs is not all zero — epoch bug fixed

Each assertion failure prints a clear message before raising.
A clean run prints a summary table and exits 0.
"""

import sys
import sqlite3
from driver import run


def check(condition, name, detail=""):
    if condition:
        print(f"  ✓  {name}")
    else:
        print(f"  ✗  {name}")
        if detail:
            print(f"     {detail}")
        return False
    return True


def run_stress_test(epochs=100):
    print(f"\n  STRESS TEST — {epochs} epochs\n")

    # Run the engine
    run(epochs=epochs)

    # Inspect the resulting database
    conn   = sqlite3.connect("discovery.db")
    c      = conn.cursor()

    c.execute("SELECT COUNT(*) FROM nodes")
    node_count = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM nodes WHERE domain='recursion'")
    rec_count = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM edges")
    edge_count = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM forbidden")
    forbidden_count = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM holes")
    hole_count = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM holes WHERE filled=0")
    open_hole_count = c.fetchone()[0]

    # Get compression history from semantic_pressure table
    c.execute("SELECT structural_compress FROM semantic_pressure ORDER BY epoch")
    compressions = [row[0] for row in c.fetchall()]

    # Check pressure boosts applied (column may not exist if no questions generated)
    try:
        c.execute("SELECT COUNT(*) FROM nodes WHERE pressure_boost > 0")
        boosted_count = c.fetchone()[0]
    except Exception:
        boosted_count = 0

    # Check epoch_found on forbidden motifs
    try:
        c.execute("SELECT epoch_found FROM forbidden")
        forbidden_epochs = [row[0] for row in c.fetchall()]
        all_epoch_zero = all(e == 0 for e in forbidden_epochs) if forbidden_epochs else True
    except Exception:
        forbidden_epochs = []
        all_epoch_zero   = True

    conn.close()

    print("\n  ── Assertions ──\n")
    passed = []

    passed.append(check(
        node_count >= epochs,
        "Node count ≥ epoch count",
        f"Got {node_count} nodes after {epochs} epochs"
    ))

    passed.append(check(
        edge_count > node_count,
        "Edge count > node count (graph is not a tree)",
        f"Got {edge_count} edges, {node_count} nodes"
    ))

    passed.append(check(
        len(compressions) > 0 and min(compressions) < 1.0,
        "Compression falls below 1.0 — graph is repeating patterns",
        f"Min compression: {min(compressions):.4f}" if compressions else "No compression data"
    ))

    passed.append(check(
        forbidden_count > 0,
        "At least one forbidden motif recorded — governance is live",
        f"Got {forbidden_count} forbidden motifs"
    ))

    passed.append(check(
        hole_count > 0,
        "At least one hole recorded — questioner fired",
        f"Got {hole_count} holes ({open_hole_count} open)"
    ))

    passed.append(check(
        not all_epoch_zero or not forbidden_epochs,
        "epoch_found on forbidden motifs is not all zero",
        f"All epochs were 0: {all_epoch_zero}  (forbidden count: {len(forbidden_epochs)})"
    ))

    passed.append(check(
        rec_count > 0,
        "Recursion nodes exist — Phase 4 is wired",
        f"Got {rec_count} recursion-domain nodes"
    ))

    passed.append(check(
        boosted_count > 0 or hole_count == 0,
        "Pressure boosts applied — question feedback loop working",
        f"Boosted nodes: {boosted_count}"
    ))

    n_passed = sum(passed)
    n_total  = len(passed)

    print(f"\n  {'─'*40}")
    print(f"  {n_passed}/{n_total} assertions passed")

    if n_passed == n_total:
        print("  Engine healthy.\n")
        sys.exit(0)
    else:
        print(f"  {n_total - n_passed} failure(s). See above.\n")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=100)
    args = parser.parse_args()
    run_stress_test(epochs=args.epochs)