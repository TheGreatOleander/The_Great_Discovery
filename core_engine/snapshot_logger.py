
import json
from datetime import datetime

def log_snapshot(state, path="recursion_log.json"):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "state": state
    }
    with open(path, "a") as f:
        f.write(json.dumps(entry) + "\n")
