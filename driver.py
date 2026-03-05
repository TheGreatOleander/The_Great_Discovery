"""
driver.py — Phase 4 (hardened)
The Great Discovery

Changes from previous version:

1. BUG FIX — _perturbation_explore() degree calculation.
   Previous SQL used COUNT(e.src) + COUNT(e.dst) in a LEFT JOIN, which
   double-counts nodes appearing as both edge source and destination.
   Fixed with a UNION-based subquery that counts each edge appearance once.

2. EXPANDING STATE — new convergence state handled.
   EXPANDING: compression flat, hole density growing. Topology stable but
   generating structural demands faster than it fills them.
   Response: reduce settle_limit to 1 (let holes accumulate and sharpen
   rather than filling them immediately). Distinct from DEADLOCKED which
   injects perturbation — here the engine isn't frozen, it's hungry.

3. CONVERGENCE STATE DISPLAY — five states in conv_label.
   EXPANDING gets label "→ Expanding" to indicate forward movement.
"""

import time
import argparse
from core_engine import init_db
from explorer import explore
from settler import settle_holes
from pressure_engine import pressure_snapshot
from governance import detect_forbidden
from hole_detector import find_nameable_holes
from questioner import generate_questions, generate_meta_questions, decay_pressure_boosts
from convergence import (ConvergenceDetector,
                         STABLE, DIVERGENT, DEADLOCKED, EXPANDING, OSCILLATORY)
from recursion import run_recursion_step


# ── Mismatch governance thresholds ───────────────────────────────────────────
MISMATCH_WARN_THRESHOLD  = 0.25   # Throttle settling to 1/epoch
MISMATCH_HALT_THRESHOLD  = 0.40   # Suspend settling entirely


_asked_holes = set()


def _hole_density(conn):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM holes WHERE filled=0")
    unfilled = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM holes")
    total = c.fetchone()[0]
    return unfilled / total if total else 0.0


def _perturbation_explore(conn, epoch):
    """
    Inject a perturbation node when the engine is DEADLOCKED.

    Targets the genuinely lowest-degree node using a UNION-based degree
    count that avoids double-counting nodes appearing as both src and dst.

    Degree = number of distinct edges touching a node, regardless of direction.
    """
    from semantics import sample_concept, sample_relation, relation_weight

    c = conn.cursor()
    concept, domain = sample_concept()
    c.execute(
        "INSERT INTO nodes (concept, domain, introduced) VALUES (?, ?, ?)",
        (concept, domain, epoch)
    )
    new_id = c.lastrowid

    # BUG FIX: use UNION to count each edge appearance once per node
    # (LEFT JOIN with COUNT(src) + COUNT(dst) double-counts nodes that
    #  appear as both src and dst in the edge table)
    c.execute("""
        SELECT n.id, n.domain, COUNT(e.node_id) as deg
        FROM nodes n
        LEFT JOIN (
            SELECT src AS node_id FROM edges
            UNION ALL
            SELECT dst AS node_id FROM edges
        ) e ON e.node_id = n.id
        WHERE n.id != ?
        GROUP BY n.id
        ORDER BY deg ASC
        LIMIT 1
    """, (new_id,))
    row = c.fetchone()
    if row:
        target_id, target_domain = row[0], row[1]
        rel    = sample_relation(domain, target_domain)
        weight = relation_weight(rel)
        c.execute("INSERT INTO edges VALUES (?, ?, ?, ?)",
                  (new_id, target_id, rel, weight))

    conn.commit()
    return concept, domain


def _oscillation_temperature(base_temp, epoch, period):
    """
    Modulate exploration temperature in phase with a detected oscillation.

    First half of each cycle (phase < period//2):
        raise temperature — push out of the rut.
    Second half (phase >= period//2):
        lower temperature — let new structure settle.
    """
    if period is None or period < 2:
        return base_temp
    phase = epoch % period
    if phase < period // 2:
        return min(base_temp + 0.2, 0.8)
    else:
        return max(base_temp - 0.1, 0.2)


def run(epochs=60):
    conn     = init_db()
    detector = ConvergenceDetector(
        window=8,
        convergence_threshold=0.01,
        divergence_threshold=0.15,
        autocorr_threshold=0.6
    )

    last_compression  = 1.0
    last_mismatch     = 0.0
    forbidden_count   = 0
    question_count    = 0
    meta_q_count      = 0
    meta_hole_count   = 0
    mismatch          = 0.0

    print("\n  THE GREAT DISCOVERY — Phase 4 (hardened)")
    print("  Forbidden repulsion · Hole attraction · Question feedback")
    print("  Recursion · Meta-questions · Mismatch governance · Oscillation control\n")

    header = (
        f"{'Epoch':>6}  {'S.Comp':>7}  {'Sem.C':>7}  "
        f"{'Mismatch':>9}  {'Entropy':>8}  {'Delta':>7}  "
        f"{'Conv.State':<16}  Event"
    )
    print(header)
    print("-" * 117)

    for epoch in range(epochs):
        conv_summary = detector.summary()
        conv_state   = conv_summary.get('state', 'Exploring')
        osc_period   = conv_summary.get('oscillation_period')

        # ── Exploration temperature ───────────────────────────────────────────
        if conv_state == DIVERGENT:
            temperature = 0.6
        elif conv_state == DEADLOCKED:
            temperature = 0.5
        elif conv_state == OSCILLATORY and osc_period:
            temperature = _oscillation_temperature(0.4, epoch, osc_period)
        else:
            temperature = 0.4

        # ── Core growth ───────────────────────────────────────────────────────
        explore(conn, epoch=epoch, temperature=temperature)

        # ── State-specific responses ──────────────────────────────────────────
        perturbation_event = None

        if conv_state == DEADLOCKED:
            # Frozen: inject perturbation to break symmetry
            pconcept, pdomain = _perturbation_explore(conn, epoch)
            perturbation_event = f"◈ PERTURBATION → '{pconcept}' ({pdomain})"

        # ── Settling — governed by mismatch and convergence state ─────────────
        if last_mismatch >= MISMATCH_HALT_THRESHOLD:
            settle_limit = 0                    # mismatch critical: suspend
        elif last_mismatch >= MISMATCH_WARN_THRESHOLD:
            settle_limit = 1                    # mismatch high: throttle
        elif conv_state == EXPANDING:
            settle_limit = 1                    # hungry: let holes sharpen
        else:
            settle_limit = 3                    # normal

        if settle_limit > 0:
            settle_holes(conn, epoch, limit=settle_limit)

        decay_pressure_boosts(conn)

        # ── Pressure measurement ──────────────────────────────────────────────
        compression, entropy, semantic_compress, mismatch = pressure_snapshot(conn, epoch)
        detect_forbidden(conn, compression, last_compression, epoch=epoch)
        last_mismatch = mismatch

        delta            = compression - last_compression
        last_compression = compression

        # ── Convergence ───────────────────────────────────────────────────────
        h_density    = _hole_density(conn)
        conv_state   = detector.record(compression, h_density)
        conv_summary = detector.summary()
        osc_period   = conv_summary.get('oscillation_period')

        if conv_state == DIVERGENT:
            conv_label = f"⚠ {conv_state}"
        elif conv_state == STABLE:
            conv_label = f"✓ {conv_state}"
        elif conv_state == DEADLOCKED:
            conv_label = f"◈ {conv_state}"
        elif conv_state == EXPANDING:
            conv_label = f"→ {conv_state}"
        elif conv_state == OSCILLATORY and osc_period:
            conv_label = f"~ {conv_state}({osc_period})"
        else:
            conv_label = conv_state

        events = []

        if perturbation_event:
            events.append(perturbation_event)

        # Mismatch governance event
        if mismatch >= MISMATCH_HALT_THRESHOLD:
            events.append(f"⚠ MISMATCH {mismatch:.3f} — settling suspended")
        elif mismatch >= MISMATCH_WARN_THRESHOLD:
            events.append(f"~ mismatch {mismatch:.3f} — settling throttled")

        # Forbidden detection
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM forbidden")
        new_forbidden_total = c.fetchone()[0]
        if new_forbidden_total > forbidden_count:
            forbidden_count = new_forbidden_total
            events.append(f"⚡ FORBIDDEN #{forbidden_count}  Δ={delta:+.3f}")

        # ── Question generation ───────────────────────────────────────────────
        questions = []
        meta_qs   = []

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
                events.append(
                    f"◉ Q#{question_count} [{q['type'].upper()}] "
                    f"boost→ nodes {q['src_id']},{q['dst_id']}"
                )

            if questions:
                meta_holes, q_node_ids = run_recursion_step(
                    conn, epoch, questions, depth=0
                )
                new_meta_holes = [mh for mh in meta_holes
                                  if mh not in _asked_holes]

                if new_meta_holes:
                    meta_hole_count += len(new_meta_holes)
                    events.append(
                        f"↻ {len(new_meta_holes)} meta-hole(s) "
                        f"[total: {meta_hole_count}]"
                    )

                    meta_qs = generate_meta_questions(conn, epoch, new_meta_holes)

                    for mq in meta_qs:
                        meta_q_count += 1
                        _asked_holes.add((mq['src_id'], mq['dst_id']))
                        events.append(f"↻↻ MQ#{meta_q_count} [META] depth=1")

                    if meta_qs:
                        run_recursion_step(conn, epoch, meta_qs, depth=1)

        # ── Output ────────────────────────────────────────────────────────────
        event_str = events[0] if events else ""
        print(
            f"{epoch:>6}  {compression:>7.4f}  {semantic_compress:>7.4f}  "
            f"{mismatch:>9.4f}  {entropy:>8.4f}  {delta:>+7.4f}  "
            f"{conv_label:<16}  {event_str}"
        )
        for e in events[1:]:
            print(f"{'':>92}  {e}")

        if questions:
            for i, q in enumerate(questions):
                qn = question_count - len(questions) + i + 1
                print(f"\n  {'─'*105}")
                print(f"  ◉  Q#{qn}  [{q['type'].upper()}]  "
                      f"precision={q['precision']:.2f}  "
                      f"domains: {' × '.join(q['domains'])}")
                print(f"  {q['question']}")
                if q.get('q_node_id'):
                    print(f"  ↻  node #{q['q_node_id']} [recursion, depth=0]")
                print(f"  {'─'*105}\n")

        if meta_qs:
            for i, mq in enumerate(meta_qs):
                mqn = meta_q_count - len(meta_qs) + i + 1
                print(f"\n  {'═'*105}")
                print(f"  ↻↻  MQ#{mqn}  [META]  precision={mq['precision']:.2f}  "
                      f"domains: {' × '.join(mq['domains'])}")
                print(f"  {mq['question']}")
                if mq.get('q_node_id'):
                    print(f"  ↻↻  node #{mq['q_node_id']} [recursion, depth=1]")
                print(f"  {'═'*105}\n")

        if conv_state == DIVERGENT:
            print(f"  ⚠  DIVERGENT — temperature {temperature:.1f}")
        elif conv_state == DEADLOCKED:
            print(f"  ◈  DEADLOCKED — perturbation injected, temperature {temperature:.1f}")
        elif conv_state == EXPANDING:
            print(f"  →  EXPANDING — holes growing, settling throttled to {settle_limit}/epoch")
        elif conv_state == OSCILLATORY and osc_period:
            print(f"  ~  OSCILLATORY period={osc_period} — temperature {temperature:.2f}")

        time.sleep(0.05)

    # ── Final summary ─────────────────────────────────────────────────────────
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM nodes");                          node_count      = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM nodes WHERE domain='recursion'"); rec_count       = c.fetchone()[0]
    try:
        c.execute("SELECT COUNT(*) FROM nodes WHERE depth=1");        meta_node_count = c.fetchone()[0]
    except Exception:
        meta_node_count = 0
    c.execute("SELECT COUNT(*) FROM edges");                          edge_count      = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM motifs");                         motif_count     = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM forbidden");                      forbidden_total = c.fetchone()[0]
    c.execute("SELECT epoch_found, demands FROM holes WHERE filled=0 ORDER BY epoch_found")
    open_holes = c.fetchall()

    final = detector.summary()

    print("\n" + "=" * 117)
    print(f"  Nodes (total):           {node_count}")
    print(f"  Nodes (recursion):       {rec_count}   ← question nodes")
    print(f"  Nodes (meta, depth=1):   {meta_node_count}   ← questions about questions")
    print(f"  Edges:                   {edge_count}")
    print(f"  Motifs observed:         {motif_count}")
    print(f"  Forbidden motifs:        {forbidden_total}")
    print(f"  Questions asked:         {question_count}")
    print(f"  Meta-questions asked:    {meta_q_count}")
    print(f"  Meta-holes detected:     {meta_hole_count}")
    print(f"  Open holes:              {len(open_holes)}")
    print(f"  Final compression:       {last_compression:.4f}")
    print(f"  Final mismatch:          {mismatch:.4f}")
    print(f"  Convergence state:       {final['state']}")
    if final.get('mean_delta_c') is not None:
        print(f"  Mean |ΔC| (last W):      {final['mean_delta_c']}")
    if final.get('mean_delta_h') is not None:
        print(f"  Mean ΔH  (last W):       {final['mean_delta_h']}")
    if final.get('oscillation_period'):
        print(f"  Oscillation period:      {final['oscillation_period']} epochs")

    if open_holes:
        print(f"\n  — Open Questions —")
        for epoch_found, demand in open_holes:
            print(f"\n  E{epoch_found:>3}: {demand}")

    if rec_count > 0:
        print(f"\n  — Recursion layer —")
        print(f"  {rec_count} question node(s) in topology  "
              f"({meta_node_count} at depth=1)")
        if meta_q_count > 0:
            print(f"  The engine has begun asking questions about its own asking.")

    print("=" * 117 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="The Great Discovery — Phase 4")
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--demo",   type=str, default=None)
    args = parser.parse_args()

    if args.demo == "governance":
        from demos.governance_demo import run_demo
        run_demo()
    else:
        run(epochs=args.epochs)
