
def generate_hypotheses(graph):

    hypotheses = []

    for e in graph.edges:
        for f in graph.edges:

            if e["b"] == f["a"]:

                h = f"If {e['a']} {e['relation']} {e['b']} and {f['a']} {f['relation']} {f['b']}, then {e['a']} may relate to {f['b']}."

                hypotheses.append(h)

    return hypotheses
