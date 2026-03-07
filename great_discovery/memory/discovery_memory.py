class DiscoveryMemory:

    def __init__(self):
        self.archive_store = {}
        self.seen = set()

    def archive(self, discovery):

        # prevent duplicate discoveries
        if discovery["id"] in self.seen:
            return False

        self.seen.add(discovery["id"])
        self.archive_store[discovery["id"]] = discovery
        return True

    def archive_all(self):
        return list(self.archive_store.values())