
# Discovery Engine Design

The discovery engine operates through interacting subsystems.

Subsystems:

1. Knowledge Graph
2. Pressure Field
3. Investigator Agents
4. Hypothesis Generator
5. Simulation/Test Layer
6. Memory + Lineage Tracking

Discovery Process:

Topology → Pressure → Investigation → Hypothesis → Validation

Investigators include:

• theorem investigator
• analogy investigator
• cross‑domain investigator
• LLM investigator

Each investigator proposes candidate discoveries which are then
evaluated for:

- novelty
- consistency
- explanatory power

Accepted discoveries update the knowledge graph.

Rejected hypotheses are archived to avoid repeated exploration.
