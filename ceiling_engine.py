
from questions.question_dynamics import generate_questions
from investigation.investigation_manager import InvestigationManager
from hole_detector import find_nameable_holes
from pressure_engine import compute_pressure
from memory.discovery_archive import DiscoveryArchive

class CeilingDiscoveryEngine:

    def __init__(self, graph, investigators, constitution):
        self.graph = graph
        self.constitution = constitution
        self.investigator_manager = InvestigationManager(investigators)
        self.archive = DiscoveryArchive()
        self.step_count = 0

    def step(self):

        # 1 Detect structural holes
        holes = find_nameable_holes(self.graph)

        # 2 Compute pressure field
        pressure = compute_pressure(self.graph, holes)

        # 3 Generate research questions
        questions = generate_questions(self.graph, holes, pressure)

        # 4 Run investigators
        hypotheses = self.investigator_manager.run(questions)

        valid = []

        # 5 Validate hypotheses against constitution
        for h in hypotheses:
            if self.constitution.validate(self.graph, h):
                valid.append(h)

        # 6 Apply graph mutations
        for h in valid:
            if "edge" in h:
                a,b = h["edge"]
                self.graph.add_edge(a,b)

        # 7 Archive discoveries
        for h in valid:
            self.archive.record(h)

        self.step_count += 1

        return {
            "holes": len(holes),
            "pressure": pressure,
            "discoveries": len(valid),
            "step": self.step_count
        }
