
import json
import hashlib

class ReplayEngine:
    def __init__(self):
        self.snapshots = []

    def snapshot(self, state):
        encoded = json.dumps(state, sort_keys=True)
        hash_val = hashlib.sha256(encoded.encode()).hexdigest()
        self.snapshots.append((hash_val, state))
        return hash_val

    def replay(self):
        return self.snapshots
