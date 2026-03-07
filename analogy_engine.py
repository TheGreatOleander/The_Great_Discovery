def detect_analogies(edges):

    results = []

    outgoing = {}

    for src, dst in edges:

        if src not in outgoing:
            outgoing[src] = set()

        outgoing[src].add(dst)

    nodes = list(outgoing.keys())

    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):

            a = nodes[i]
            b = nodes[j]

            a_targets = outgoing[a]
            b_targets = outgoing[b]

            shared = a_targets.intersection(b_targets)

            if len(shared) >= 1:

                a_unique = a_targets - shared
                b_unique = b_targets - shared

                for x in a_unique:
                    for y in b_unique:

                        results.append((a, y))
                        results.append((b, x))

    # remove duplicates
    results = list(set(results))

    return results