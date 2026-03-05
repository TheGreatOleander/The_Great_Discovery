# The Great Discovery
### Architecture & Mechanics

*This document describes how the engine works — structurally, mechanically, and conceptually. It is written for builders, but layered so that non-builders can follow the logic. If a term is unfamiliar, consult the Glossary.*

---

## Overview

The Great Discovery is a closed-loop constraint engine built around a growing knowledge graph. It does not store knowledge. It maps the structural shape that knowledge implies by accumulating forbidden configurations and watching what the remaining topology demands.

The engine runs in epochs. Each epoch:
1. The graph grows
2. Structural pressure is measured
3. Forbidden patterns are detected and recorded
4. The state is updated and the cycle repeats

Nothing is forced. Everything settles — or signals that it won't.

---

## The Five Components

### 1. Core Engine (`core_engine.py`)
Initializes and maintains the persistent state of the system in a SQLite database.

**Tables:**
- `nodes` — every point in the graph
- `edges` — every connection between points
- `motifs` — every structural pattern observed, with frequency and last-seen epoch
- `forbidden` — every pattern flagged as a table edge, with spike magnitude

The database is the table. Everything the engine knows about its own structure lives here. It persists across runs, accumulates across time. The engine does not forget.

---

### 2. Explorer (`explorer.py`)
Grows the graph — adds new nodes and edges each epoch.

**Two mechanisms:**

*Organic growth:* Each epoch, a new node is added and connected to an existing node. Currently random; future implementations will bias toward structurally underrepresented regions — toward the holes.

*Hole allocation:* After organic growth, the explorer performs transitive closure — if A connects to B, and B connects to C, and A does not connect to C, that potential edge is a candidate for addition. This is the embryonic form of the hole-filling mechanic. The graph is completing itself, not being completed.

**The critical future development:** Hole allocation should not be transitive closure (pure logic). It should be energy minimization — the surrounding structure exerts pressure, and the right connection settles into place because all others are forbidden. This is where Floquet dynamics and perturbation theory enter the architecture.

---

### 3. Pressure Engine (`pressure_engine.py`)
Measures the structural state of the graph each epoch.

**Process:**
1. Sample subgraphs of size N (currently N=3) from all node combinations
2. Compute the canonical signature of each subgraph
3. Count unique signatures vs. total observations → **compression ratio**
4. Compute Shannon entropy of the signature distribution → **entropy**
5. Store all motif observations in the database

**What it produces:**
- Compression ratio: how much the graph is repeating its own patterns
- Entropy: how evenly distributed those patterns are

Together these give the engine its sense of where it is in the settling process — still exploring, beginning to converge, or straining against its own constraints.

**Known scaling constraint:** Sampling all combinations of N nodes is O(n^N). At N=3 this becomes expensive quickly as the graph grows. Future implementations will sample a rolling window of recent nodes, or use importance-weighted sampling biased toward structurally significant regions.

---

### 4. Governance (`governance.py`)
Watches for compression spikes — sudden sharp increases in compression ratio between epochs.

When a spike exceeds the threshold:
1. The most prevalent motif at the moment of the spike is identified
2. It is recorded in the `forbidden` table with the spike's magnitude
3. The engine now knows one more thing that destabilizes the topology

Governance does not stop the engine. It does not redirect it. It does not raise an alarm. It **records**. The accumulation of forbidden motifs is the engine's memory of where the walls are — and walls are what give holes their shape.

**The threshold** (currently 0.15) is a tunable parameter. Too low and ordinary fluctuations pollute the forbidden table. Too high and genuine structural edges are missed. Calibrating this threshold is part of the engine's ongoing development.

---

### 5. Driver (`driver.py`)
Orchestrates the epoch loop. Calls each component in sequence, tracks compression delta between epochs, and reports state.

Simple now. Will grow as the engine develops feedback mechanisms — the ability not just to observe pressure but to respond to it.

---

## The Feedback Loop

```
GROW → MEASURE → GOVERN → UPDATE → GROW → ...
       ↑                      |
       └──── forbidden ────────┘
             accumulates
             holes sharpen
             map becomes opinionated
```

This is the whole engine. It is closed. It feeds itself. Each pass leaves it more constrained than before — which means each pass leaves it more precise.

---

## Current Limitations (Honest Accounting)

**Nodes are anonymous.** They carry IDs but no meaning. The engine is operating on pure topology — it can find structural patterns but cannot yet say what those patterns mean. The abstraction layer — the semantic weight that will let nodes carry concepts and edges carry relationship types — is the next major development.

**Signatures are not isomorphism-invariant.** Two structurally identical subgraphs with different node IDs produce different signatures. This means the motif vocabulary is larger than the true structural vocabulary. Correcting this requires canonical graph isomorphism — a known hard problem with practical approximations.

**Hole allocation is logic, not physics.** Transitive closure fills gaps by inference. True settling requires energy minimization — the hole exerts a demand, the surrounding structure exerts pressure, and the right concept relaxes into place. This is the most important unsolved mechanical problem in the current implementation.

**Exploration has no bias toward holes.** New nodes are added without regard for where the structural pressure is highest. Future exploration should be drawn toward structurally underrepresented regions — toward where the holes are.

---

## The Road Not Yet Built

The current engine is structurally-only. No semantics. No abstraction. No meaning.

This is intentional. The dynamics must be correct before meaning is introduced. A pressure engine that misbehaves on pure topology will misbehave worse when concepts are loaded in.

When the structural dynamics are validated, the next layer introduces:

- **Typed nodes** — carrying meaning anchors (concepts, domains, questions)
- **Typed edges** — carrying relationship types (causes, contradicts, requires, emerges from)
- **Semantic pressure** — compression and entropy measured not just structurally but conceptually
- **Named holes** — when a hole's shape becomes precise enough, the engine surfaces it as a question in language
- **True settling** — energy minimization replacing transitive closure in hole allocation

At that point, the engine stops being a structural curiosity and starts being what it was always meant to be:

**A map that asks questions the mapmaker hasn't thought to ask yet.**
