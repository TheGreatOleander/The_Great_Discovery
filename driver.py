"""
driver.py — Phase 3 hardened + Phase 4 seed
The Great Discovery

Three new things wired in this version:

1. EXPLORATION BIAS — explorer.py now reads forbidden and holes tables
   when building the pressure field. New nodes are steered toward open
   holes and away from forbidden-adjacent zones.

2. QUESTION FEEDBACK — after each question is generated, pressure boosts
   are applied to the nodes it's about. The engine circles back and
   explores more aggressively near unanswered holes. Boosts decay at
   0.15/epoch.

3. RECURSION SEED — question nodes are injected into the graph as real
   nodes (domain='recursion'). They participate in motif sampling and
   hole detection. When the question layer develops holes of its own,
   those are meta-questions: questions the pattern of asking questions
   implies but hasn't yet asked. Phase 4 begins here.
"""

import time
import argparse
from core_engine import init_db
from explorer import explore, build_pressure_field
from settler import settle_holes
from pressure_engine import pressure_snapshot
from governance import detect_forbidden
from hole_detector import find_nameable_holes
from questioner import generate_questions, decay_pressure_boosts
from convergence import ConvergenceDetector, STABLE, DIVERGENT, DEADLOCKED
from recursion import run_recursion_step


_asked_holes = set()


def _hole_density(conn):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM holes WHERE filled=0")
    unfilled = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM holes")
    total    = c.fetchone()[0]
    return unfilled / total if total else 0.0


def run(epochs=60):
    conn     = init_db()
    detector = ConvergenceDetector(
        window=8,
        convergence_threshold=0.01,
        divergence_threshold=0.15,
        autocorr_threshold=0.6
    )

    last_compression  = 1.0
    forbidden_count   = 0
    question_count    = 0
    meta_hole_count   = 0
    mismatch          = 0.0

    print("\n  THE GREAT DISCOVERY — Phase 3 hardened + Phase 4 seed")
    print("  Forbidden repulsion. Hole attraction. Question feedback. Recursion layer.\n")

    header = (
        f"{'Epoch':>6}  {'S.Comp':>7}  {'Sem.C':>7}  "
        f"{'Mismatch':>9}  {'Entropy':>8}  {'Delta':>7}  "
        f"{'Conv.State':<14}  Event"
    )
    print(header)
    print("-" * 115)

    for epoch in range(epochs):
        # ── Convergence state → exploration temperature ───────────────────────
        conv_summary = detector.summary()
        # When diverging, raise temperature to increase exploration diversity
        temperature = 0.6 if conv_summary.get('state') == DIVERGENT else 0.4

        # ── Core epoch ────────────────────────────────────────────────────────
        explore(conn, epoch=epoch, temperature=temperature)
        settle_holes(conn, epoch, limit=3)

        # Decay question pressure boosts each epoch
        decay_pressure_boosts(conn)

        compression, entropy, semantic_compress, mismatch = pressure_snapshot(conn, epoch)
        forbidden_sig, spike = detect_forbidden(conn, compression, last_compression)

        delta            = compression - last_compression
        last_compression = compression

        # ── Convergence detection ─────────────────────────────────────────────
        h_density  = _hole_density(conn)
        conv_state = detector.record(compression, h_density)
        conv_summary = detector.summary()

        if conv_state == DIVERGENT:
            conv_label = f"⚠ {conv_state}"
        elif conv_state == STABLE:
            conv_label = f"✓ {conv_state}"
        elif conv_state == DEADLOCKED:
            conv_label = f"◈ {conv_state}"
        else:
            conv_label = conv_state

        events = []

        if forbidden_sig:
            forbidden_count += 1
            events.append(f"⚡ FORBIDDEN #{forbidden_count}  spike={spike:.3f}")

        # ── Question generation + recursion ───────────────────────────────────
        questions  = []
        meta_holes = []

        if epoch >= 8 and epoch % 5 == 0:
            profiles     = find_nameable_holes(conn, limit=2)
            new_profiles = [
                p for p in profiles
                if (p['src_id'], p['dst_id']) not in _asked_holes
            ]
            for p in new_profiles:
                _asked_holes.add((p['src_id'], p['dst_id']))

            questions = generate_questions(conn, epoch, new_profiles)

            for q in questions:
                question_count += 1
                events.append(f"◉ Q#{question_count} [{q['type'].upper()}] "
                               f"boost→ nodes {q['src_id']},{q['dst_id']}")

            # Recursion step: inject question nodes, find meta-holes
            if questions:
                meta_holes, q_node_ids = run_recursion_step(conn, epoch, questions)
                new_meta = [mh for mh in meta_holes
                            if mh not in _asked_holes]
                if new_meta:
                    meta_hole_count += len(new_meta)
                    events.append(f"↻ {len(new_meta)} meta-hole(s) detected  "
                                  f"[total: {meta_hole_count}]")

        # ── Output ────────────────────────────────────────────────────────────
        event_str = events[0] if events else ""
        print(
            f"{epoch:>6}  {compression:>7.4f}  {semantic_compress:>7.4f}  "
            f"{mismatch:>9.4f}  {entropy:>8.4f}  {delta:>+7.4f}  "
            f"{conv_label:<14}  {event_str}"
        )
        for e in events[1:]:
            print(f"{'':>90}  {e}")

        if questions:
            for i, q in enumerate(questions):
                qn = question_count - len(questions) + i + 1
                print(f"\n  {'─'*105}")
                print(f"  ◉  Q#{qn}  [{q['type'].upper()}]  "
                      f"precision={q['precision']:.2f}  "
                      f"domains: {' × '.join(q['domains'])}")
                print(f"  {q['question']}")
                if q.get('q_node_id'):
                    print(f"  ↻  Injected as graph node #{q['q_node_id']} "
                          f"[domain=recursion, depth=0]")
                print(f"  {'─'*105}\n")

        if conv_state == DIVERGENT:
            print(f"  ⚠  DIVERGENT — raising exploration temperature to {temperature:.1f}")
        elif conv_state == DEADLOCKED:
            period = conv_summary.get('oscillation_period')
            msg = "  ◈  DEADLOCKED"
            if period:
                msg += f" — oscillation period: {period} epochs"
            print(msg)

        time.sleep(0.05)

    # ── Final summary ─────────────────────────────────────────────────────────
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM nodes");                          node_count      = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM nodes WHERE domain='recursion'"); rec_count       = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM edges");                          edge_count      = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM motifs");                         motif_count     = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM forbidden");                      forbidden_total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM holes");                          hole_count      = c.fetchone()[0]
    c.execute("SELECT epoch_found, demands FROM holes WHERE filled=0 ORDER BY epoch_found")
    open_holes = c.fetchall()

    final = detector.summary()

    print("\n" + "=" * 115)
    print(f"  Nodes (total):       {node_count}")
    print(f"  Nodes (recursion):   {rec_count}  ← question nodes in graph")
    print(f"  Edges:               {edge_count}")
    print(f"  Motifs observed:     {motif_count}")
    print(f"  Forbidden motifs:    {forbidden_total}")
    print(f"  Questions asked:     {question_count}")
    print(f"  Meta-holes detected: {meta_hole_count}")
    print(f"  Open holes:          {len(open_holes)}")
    print(f"  Final compression:   {last_compression:.4f}")
    print(f"  Final mismatch:      {mismatch:.4f}")
    print(f"  Convergence state:   {final['state']}")
    if final.get('mean_delta_c') is not None:
        print(f"  Mean |ΔC| (last W):  {final['mean_delta_c']}")
    if final.get('oscillation_period'):
        print(f"  Oscillation period:  {final['oscillation_period']} epochs")

    if open_holes:
        print(f"\n  — Open Questions (unfilled holes) —")
        for epoch_found, demand in open_holes:
            print(f"\n  E{epoch_found:>3}: {demand}")

    if rec_count > 0:
        print(f"\n  — Recursion layer active —")
        print(f"  {rec_count} question node(s) are now part of the topology.")
        print(f"  The engine is beginning to map its own discovery process.")

    print("=" * 115 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="The Great Discovery — Phase 3+4")
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--demo",   type=str, default=None)
    args = parser.parse_args()

    if args.demo == "governance":
        from demos.governance_demo import run_demo
        run_demo()
    else:
        run(epochs=args.epochs)