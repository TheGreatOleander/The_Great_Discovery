
import networkx as nx

def export_graphviz(graph, path="graph.dot"):
    nx.drawing.nx_pydot.write_dot(graph, path)
