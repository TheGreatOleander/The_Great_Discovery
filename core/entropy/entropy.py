
import random

def inject_entropy(nodes):
    return random.choice(list(nodes)) if nodes else None
