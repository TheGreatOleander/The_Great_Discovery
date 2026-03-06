
from core.discovery_engine import DiscoveryEngine
from topology.knowledge_topology import KnowledgeTopology
from pressure.pressure_field import PressureField
from investigators.analogy_investigator import AnalogyInvestigator
from investigators.theorem_investigator import TheoremInvestigator
from memory.discovery_archive import DiscoveryArchive
import random

topology = KnowledgeTopology()
pressure = PressureField()
memory = DiscoveryArchive()

for i in range(10):
    topology.add_node(f"concept_{i}")

for i in range(9):
    topology.add_edge(f"concept_{i}",f"concept_{i+1}")

for n in topology.nodes:
    pressure.add_pressure(n,random.random())

engine = DiscoveryEngine(
    topology,
    pressure,
    [AnalogyInvestigator(),TheoremInvestigator()],
    memory
)

for i in range(20):

    discoveries = engine.step()

    print("iteration",i,"discoveries",discoveries)

print("total discoveries",memory.summary())
