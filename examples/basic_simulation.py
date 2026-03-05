
from kernel import EngineState, Constitution, GreatDiscoveryEngine, run_simulation

def hole_detector(state):
    return []

def pressure_metric(state):
    return 1.0

def entropy_metric(state):
    return 0.5

def governance_mutator(state):
    if isinstance(state.governance, dict):
        for k in state.governance:
            if isinstance(state.governance[k], (int, float)):
                state.governance[k] += 0.01

graph = {}
governance = {"stability": 1.0}
invariants = {}

state = EngineState(graph, governance, invariants)
constitution = Constitution()

engine = GreatDiscoveryEngine(
    state,
    constitution,
    hole_detector,
    pressure_metric,
    entropy_metric,
    governance_mutator
)

run_simulation(engine, steps=10)

print(state.history)
