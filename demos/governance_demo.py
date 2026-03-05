
import numpy as np
from core_structural.system_model import StructuralSystem

def run_demo():
    system = StructuralSystem()

    # Actors
    system.graph.add_actor("Legislature")
    system.graph.add_actor("Executive")
    system.graph.add_actor("Judiciary")

    # Relations
    system.graph.add_relation("Legislature", "Executive", 1.0)
    system.graph.add_relation("Executive", "Judiciary", 1.0)
    system.graph.add_relation("Judiciary", "Legislature", 0.5)

    # Constraints
    system.constraints.add_constraint(lambda x: x[0] + x[1] - 10, weight=1.0)

    # Incentives
    system.incentives.set_global_objective(lambda x: -((x[0]-5)**2 + (x[1]-5)**2))
    system.incentives.add_actor_utility("Legislature", lambda x: -(x[0]-6)**2)
    system.incentives.add_actor_utility("Executive", lambda x: -(x[1]-4)**2)

    state = np.array([4.0, 6.0])
    results = system.evaluate(state)

    print("Pressure Score:", round(results["pressure"], 4))
    print("Fragility Index:", round(results["fragility"], 4))
    print("Incentive Divergence:", round(results["divergence"], 4))

if __name__ == "__main__":
    run_demo()
