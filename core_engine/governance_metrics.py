
import networkx as nx

def governance_influence_index(graph, governance_nodes):
    centrality = nx.betweenness_centrality(graph)
    scores = {}
    for node in governance_nodes:
        scores[node] = centrality.get(node, 0)
    return scores
