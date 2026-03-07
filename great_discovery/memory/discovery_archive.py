
class DiscoveryArchive:

    def __init__(self):
        self.discoveries = []

    def archive(self,discovery):
        self.discoveries.append(discovery)

    def summary(self):
        return len(self.discoveries)
