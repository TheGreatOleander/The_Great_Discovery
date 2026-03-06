
import json
import os

FILE = "knowledge_graph.json"

def save_graph(edges):

    with open(FILE,"w") as f:
        json.dump(edges,f)


def load_graph():

    if not os.path.exists(FILE):
        return []

    with open(FILE) as f:
        return [tuple(x) for x in json.load(f)]
