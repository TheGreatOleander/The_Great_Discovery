
import json
import os

DB_FILE = "knowledge_graph.json"

class GraphStore:

    def __init__(self):
        self.nodes = set()
        self.edges = []

    def add_edge(self,a,b,relation,weight,source):

        self.nodes.add(a)
        self.nodes.add(b)

        self.edges.append({
            "a":a,
            "b":b,
            "relation":relation,
            "weight":weight,
            "source":source
        })

    def edge_count(self):
        return len(self.edges)

    def save(self):

        with open(DB_FILE,"w") as f:

            json.dump({
                "nodes":list(self.nodes),
                "edges":self.edges
            },f,indent=2)

    @classmethod
    def load(cls):

        g = cls()

        if not os.path.exists(DB_FILE):

            seeds = [
                "wave","particle","field","mass","energy","frequency",
                "entropy","information","charge","spin","momentum",
                "time","gravity","resonance","orbit","force"
            ]

            for s in seeds:
                g.nodes.add(s)

            return g

        with open(DB_FILE) as f:
            data=json.load(f)

        g.nodes=set(data["nodes"])
        g.edges=data["edges"]

        return g
