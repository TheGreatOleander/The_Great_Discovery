
class PressureField:

    def __init__(self):
        self.values = {}

    def measure(self, node):
        return self.values.get(node,0)

    def add_pressure(self,node,value):
        self.values[node] = self.values.get(node,0)+value

    def diffuse(self,topology):
        new_values = {}

        for node,value in self.values.items():
            neighbors = topology.edges.get(node,[])
            share = value*0.2

            new_values[node] = new_values.get(node,0)+(value*0.8)

            for n in neighbors:
                new_values[n] = new_values.get(n,0)+share/len(neighbors) if neighbors else 0

        self.values = new_values
