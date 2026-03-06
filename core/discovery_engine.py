
class DiscoveryEngine:

    def __init__(self, topology, pressure_field, investigators, memory):
        self.topology = topology
        self.pressure_field = pressure_field
        self.investigators = investigators
        self.memory = memory
        self.iteration = 0

    def step(self):
        self.iteration += 1

        unstable = self.topology.detect_instability()

        discoveries = []

        for region in unstable:
            pressure = self.pressure_field.measure(region)

            investigator = sorted(self.investigators, key=lambda i: i.priority)[0]

            result = investigator.investigate(region, pressure)

            if result:
                discoveries.append(result)
                self.memory.archive(result)
                self.topology.integrate(result)

        # diffuse pressure across graph
        self.pressure_field.diffuse(self.topology)

        return discoveries
