
class DiscoveryLineage:

    def __init__(self):
        self.tree = {}

    def add(self, parent, child):
        self.tree.setdefault(parent, []).append(child)
