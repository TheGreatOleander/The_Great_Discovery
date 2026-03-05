
import json

def save_replay(state, filepath):
    with open(filepath, "w") as f:
        json.dump(state.history, f, indent=2)

def load_replay(filepath):
    with open(filepath, "r") as f:
        return json.load(f)
