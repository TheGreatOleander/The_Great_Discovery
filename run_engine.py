
from core.engine_v2 import DiscoveryEngineV2
from core.topology import KnowledgeTopology
from pressure.resonance_pressure import ResonancePressure
from investigators.analogy_investigator import AnalogyInvestigator
from memory.discovery_archive import DiscoveryArchive

topology = KnowledgeTopology()
pressures = [ResonancePressure()]
investigators = [AnalogyInvestigator()]
memory = DiscoveryArchive()

engine = DiscoveryEngineV2(topology, pressures, investigators, memory)

for _ in range(5):
    engine.step()

print("Discoveries:", memory.discoveries)
