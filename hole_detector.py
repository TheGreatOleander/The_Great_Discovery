
def find_nameable_holes(edges):

    holes = []

    for a,b in edges:
        for c,d in edges:

            if b == c and a != d:

                if (a,d) not in edges:

                    holes.append({
                        "src":a,
                        "dst":d,
                        "type":"transitive"
                    })

    return holes
