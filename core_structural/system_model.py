
from .graph_model import GraphModel
from .constraint_model import ConstraintModel
from .incentive_model import IncentiveModel

class StructuralSystem:
    def __init__(self):
        self.graph = GraphModel()
        self.constraints = ConstraintModel()
        self.incentives = IncentiveModel()

    def evaluate(self, state):
        return {
            "pressure": self.constraints.pressure(state),
            "fragility": self.graph.fragility_index(),
            "divergence": self.incentives.divergence(state)
        }
