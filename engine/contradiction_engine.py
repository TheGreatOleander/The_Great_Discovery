
def detect_contradictions(graph):
    contradictions = []

    for e in graph.edges:
        for f in graph.edges:
            if e["a"] == f["b"] and e["b"] == f["a"]:
                if e["relation"] != f["relation"]:
                    contradictions.append((e,f))

    return contradictions[:50]
