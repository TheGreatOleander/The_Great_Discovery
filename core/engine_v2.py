
class DiscoveryEngineV2:
    """Improved orchestration engine with modular pressure routing."""

    def __init__(self, topology, pressures, investigators, memory):
        self.topology = topology
        self.pressures = pressures
        self.investigators = investigators
        self.memory = memory
        self.iteration = 0

    def step(self):
        self.iteration += 1
        unstable = self.topology.detect_instability()

        for region in unstable:
            pressure = self.aggregate_pressure(region)
            investigator = self.select_investigator(region)
            result = investigator.investigate(region, pressure)

            if result:
                self.memory.archive(result)
                self.topology.integrate(result)

    def aggregate_pressure(self, region):
        score = 0
        for p in self.pressures:
            score += p.measure(region)
        return score

    def select_investigator(self, region):
        return sorted(self.investigators, key=lambda i: i.priority)[0]
