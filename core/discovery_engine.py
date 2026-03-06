import random


class DiscoveryEngine:

    def __init__(self, topology, pressure_field, investigators, memory):
        self.topology = topology
        self.pressure_field = pressure_field
        self.investigators = investigators
        self.memory = memory
        self.iteration = 0

    def step(self):

        self.iteration += 1
        discoveries = []

        # inject curiosity pressure
        for node in self.topology.nodes:
            if random.random() < 0.15:
                self.pressure_field.add_pressure(node, random.random() * 0.5)

        unstable = self.topology.detect_instability(self.pressure_field)

        for region in unstable:

            pressure = self.pressure_field.measure(region)

            for investigator in sorted(self.investigators, key=lambda i: i.priority):

                result = investigator.investigate(region, pressure)

                if not result:
                    continue

                accepted = self.memory.archive(result)

                if accepted:
                    discoveries.append(result)
                    self.topology.integrate(result)

                break

        self.pressure_field.diffuse(self.topology)

        return discoveries