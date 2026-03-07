"""
ceiling_engine.py
The Great Discovery

Wires the subsystems into a full discovery loop using the real Phase 4 pipeline.

Pipeline per step:
    holes → pressure → questions → investigators → hypotheses → validation → graph mutation → archive

Bugs fixed from original:
    - compute_pressure()           → pressure_snapshot(conn, epoch)   [function didn't exist]
    - archive.archive()             → archive.archive()                 [method didn't exist]
    - InvestigationManager(investigators) → InvestigationManager(graph) [wrong signature]
    - questions.question_dynamics  → questioner                        [deleted module]
"""

from investigation.investigation_manager import InvestigationManager
from hole_detector import find_nameable_holes
from pressure_engine import pressure_snapshot
from questioner import generate_questions
from memory.discovery_memory import DiscoveryMemory


class CeilingDiscoveryEngine:

    def __init__(self, conn, graph, constitution):
        """
        Args:
            conn        : sqlite3 connection — used by pressure_snapshot and generate_questions
            graph       : passed to InvestigationManager for investigator context
            constitution: object with validate(state, mutation_delta) → bool
        """
        self.conn = conn
        self.graph = graph
        self.constitution = constitution
        self.investigator_manager = InvestigationManager(graph)
        self.archive = DiscoveryMemory()
        self.step_count = 0

    def step(self):

        # 1. Detect structural holes
        holes = find_nameable_holes(self.conn)

        # 2. Compute pressure snapshot → (compression, entropy, semantic_compress, mismatch)
        compression, entropy, semantic_compress, mismatch = pressure_snapshot(
            self.conn, self.step_count
        )

        # 3. Generate research questions from top holes
        questions = generate_questions(self.conn, self.step_count, holes[:5])

        # 4. Run investigators against each question
        hypotheses = []
        for q in questions:
            results = self.investigator_manager.run(q.get("question", ""))
            hypotheses.extend(results)

        valid = []

        # 5. Validate hypotheses against constitution
        for h in hypotheses:
            if self.constitution.validate(self, 0.0):
                valid.append(h)

        # 6. Apply graph mutations for hypotheses that propose edges
        c = self.conn.cursor()
        for h in valid:
            if "edge" in h:
                src, dst = h["edge"]
                try:
                    c.execute(
                        "INSERT INTO edges (src, dst, relation_type, weight) VALUES (?, ?, ?, ?)",
                        (src, dst, h.get("relation", "related"), h.get("weight", 0.5))
                    )
                except Exception:
                    pass  # skip duplicate or invalid edges
        self.conn.commit()

        # 7. Archive valid discoveries (DiscoveryMemory deduplicates by id)
        for h in valid:
            if "id" not in h:
                h["id"] = f"ceiling_{self.step_count}_{len(valid)}"
            self.archive.archive(h)

        self.step_count += 1

        return {
            "holes":       len(holes),
            "compression": compression,
            "mismatch":    mismatch,
            "questions":   len(questions),
            "hypotheses":  len(hypotheses),
            "discoveries": len(valid),
            "step":        self.step_count
        }
