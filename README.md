
Discovery Engine ver+2

New Features
------------

• Persistent knowledge graph
• Entropy injection to prevent convergence
• Three discovery mechanisms:
    - logical holes
    - topology pressure
    - analogy patterns

Modules
-------

run_discovery.py      main engine loop
hole_detector.py      transitive discovery
topology_pressure.py  shared-neighbor bridges
analogy_engine.py     structural motif similarity
entropy_injection.py  exploration generator
graph_store.py        persistent knowledge graph

Run
---

python run_discovery.py

The graph will persist between runs in:

knowledge_graph.json
