# The Great Discovery
### Glossary of Terms

*Every term in this project has a precise meaning. These definitions exist so that nobody mistakes a hole for a bug, a forbidden motif for an error, or a compression spike for a failure. Read this before touching the code.*

---

## Node
A point in the knowledge graph. In the current structural implementation, nodes carry no semantic content — they are positional placeholders. In future implementations, nodes will carry **meaning anchors**: concepts, domains, archetypes, or questions. A node is not a fact. It is a location in the topology.

---

## Edge
A relationship between two nodes. Edges are currently untyped — they indicate connection without specifying its nature. Future implementations will type edges: *causes, contradicts, requires, emerges from, is a kind of, is forbidden by.* An edge is not a statement. It is a structural bond.

---

## Motif
A recurring subgraph pattern — the structural signature of a small neighborhood of nodes and edges. Motifs are the basic vocabulary of the map's topology. Two motifs with the same signature have the same structural shape, regardless of which specific nodes they contain. Motifs are how the engine recognizes that it has been somewhere before.

---

## Canonical Signature
The unique fingerprint of a motif, derived from its adjacency matrix. Two subgraphs with identical structure produce identical canonical signatures. This is how the engine compares structural patterns across different regions of the graph without caring about the specific identities of the nodes involved.

*Current limitation: signatures are not yet isomorphism-invariant across node orderings. This is a known constraint, not a bug.*

---

## Compression Ratio
The ratio of unique motif signatures to total motif observations. 

- **High compression** (ratio near 0): the graph contains many repeated structural patterns — the topology is converging, familiar, settling.
- **Low compression** (ratio near 1): the graph contains mostly novel patterns — the topology is still exploring, diverse, open.

Compression is a pressure signal. It measures how much the map has begun to repeat itself — which is not the same as how much it has learned.

---

## Entropy
The Shannon entropy of the motif distribution. Measures how evenly structural weight is distributed across known patterns.

- **High entropy**: many patterns, all roughly equally common — the system is still in open exploration.
- **Low entropy**: a few patterns dominating — the system is converging on a structural preference, a shape that keeps recurring.

Entropy falling is not failure. It is the sound of the table filling in.

---

## Compression Spike
A sudden, sharp rise in compression ratio between epochs. Indicates that the topology has encountered a configuration that rapidly homogenizes the local structure — the map suddenly looks much more like itself than it did a moment ago.

Compression spikes are the primary signal used by the governance layer. They do not mean something went wrong. They mean **the edge of the table was just found.**

---

## Forbidden Motif
A structural pattern flagged by the governance layer when a compression spike occurs. The most prevalent motif at the moment of the spike is recorded as forbidden, along with the spike's magnitude.

Forbidden motifs are not errors.
They are not dead ends.
They are **the edges of the table** — the configurations that destabilize the surrounding topology, whose presence defines, by exclusion, where the valid structure must lie.

The accumulation of forbidden motifs is how the engine develops structural taste.

---

## Hole
A load-bearing absence in the topology — a configuration the surrounding structure requires in order to remain self-consistent, which has not yet been filled.

Holes are not gaps in the data.
Holes are not missing nodes.
Holes are **structural debts** that the shape of the known graph has incurred.

Like germanium before Mendeleev named it. Like the neutrino before anyone detected it. The surrounding constraints make the hole's existence not probable but mandatory.

As the map fills and forbidden motifs accumulate, holes become more precisely shaped. A precisely shaped hole is the engine asking a question. The question is not composed in language — it is composed in topology. But it is a real question, and it demands a real answer.

---

## Pressure
The combined signal of compression, entropy, and their rates of change over time. Pressure is the engine's sense of how much structural tension the current topology is holding.

High pressure: the system is straining — too many forbidden configurations in proximity, too little diversity, the shape is fighting itself.

Low pressure: the system is relaxed — diverse, stable, settling naturally.

The engine does not minimize pressure. It reads pressure as signal. Pressure is information.

---

## Settling
The process by which a concept, relationship, or structure finds its natural position in the topology — not because it was placed there, but because the surrounding constraints made every other position forbidden.

Settling is the opposite of forcing.
Nothing in this engine is forced.
If something won't settle, that is signal too.

---

## The Table
The complete structure of constraints, forbidden motifs, holes, and settled configurations that the engine has accumulated at any given point. Named for Mendeleev's periodic table — not because knowledge is periodic, but because the method is the same: build the shape until the shape tells you what must exist.

The table is never complete.
The table is always more complete than it was.
Those two facts are not in tension.

---

## Epoch
One complete cycle of the engine: growth, pressure measurement, governance check, state update. Epochs are not units of time. They are units of discovery — each one leaving the table slightly more opinionated than before.

---

## Governance
The layer of the engine that watches for compression spikes and records forbidden motifs. Governance does not control the exploration. It does not stop the engine or redirect it. It observes, records, and accumulates the edges of the table.

Governance is the engine's memory of where the walls are.

---

## Mapmaker
The engine itself, in its recursive capacity — the aspect of the system that becomes more precise in its exploration as a result of what it has already explored. The mapmaker is not a separate component. It is what the engine becomes over time.

*The map sharpens the mapmaker. The mapmaker sharpens the map.*
