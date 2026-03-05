
def run_simulation(engine, steps=100, stop_on_violation=True):
    for _ in range(steps):
        success = engine.step()
        if stop_on_violation and not success:
            break
