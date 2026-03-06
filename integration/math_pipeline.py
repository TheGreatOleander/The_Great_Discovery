
from math.symmetry.symmetry_detector import SymmetryDetector
from math.symmetry.invariant_finder import InvariantFinder
from math.operators.operator_generator import OperatorGenerator
from math.structures.structure_discovery import StructureDiscovery
from math.analysis.theorem_generator import TheoremGenerator

class MathDiscoveryPipeline:

    def __init__(self, graph):
        self.graph = graph

    def run(self):
        sym = SymmetryDetector(self.graph).detect()
        inv = InvariantFinder(self.graph).find()
        ops = OperatorGenerator(self.graph).generate()

        structures = StructureDiscovery(sym, ops).assemble()
        theorems = TheoremGenerator(structures).propose()

        return {
            "symmetries": sym,
            "invariants": inv,
            "operators": ops,
            "structures": structures,
            "theorems": theorems
        }
