"""
api.py
The Great Discovery

Entry point that boots the kernel engine and runs a simulation.

Bug fixed: run_loop() → run_simulation() — the former never existed in kernel/loop.py
"""

from kernel.loop import run_simulation
from kernel.engine import GreatDiscoveryEngine
from kernel.state import EngineState
from kernel.constitution import Constitution


def _noop_hole_detector(state):
    return []

def _noop_pressure_metric(state):
    return 0.0

def _noop_entropy_metric(state):
    return 0.0

def _noop_governance_mutator(state):
    pass


def start(steps=60):
    print("Starting The Great Discovery — kernel engine")

    state = EngineState(
        graph={},
        governance={"stability": 1.0},
        invariants={}
    )
    constitution = Constitution()

    engine = GreatDiscoveryEngine(
        state=state,
        constitution=constitution,
        hole_detector=_noop_hole_detector,
        pressure_metric=_noop_pressure_metric,
        entropy_metric=_noop_entropy_metric,
        governance_mutator=_noop_governance_mutator,
    )

    run_simulation(engine, steps=steps)
    print(f"Done. {len(state.history)} steps recorded.")


if __name__ == "__main__":
    start()
