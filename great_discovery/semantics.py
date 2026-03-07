"""
semantics.py — Phase 2
The Great Discovery

The vocabulary of meaning anchors available to the engine.

This is not a knowledge base. These are not facts.
These are orientations — points in conceptual space that nodes
can be drawn toward. A node anchored to 'causality' is not a
database entry for causality. It is a position in the topology
that the structural pressure of surrounding nodes has made
causality-shaped.

The vocabulary is organized by domain. Domains cluster in the graph.
Edges between domains are rarer and more structurally significant
than edges within domains — they are candidates for forbidden motifs
and for the most precisely shaped holes.

Relation types define edge character. Two nodes with the same
structural connection but different relation types are different motifs.
The table becomes richer when typed edges are introduced.
"""

import random

# ── Concept vocabulary ────────────────────────────────────────────────────────
# Organized by domain. Each concept is a meaning anchor — a word or phrase
# that orients a node without defining it completely.

CONCEPTS = {
    "physics": [
        "causality", "symmetry", "entropy", "energy", "field",
        "wave", "particle", "force", "spacetime", "equilibrium",
        "phase transition", "conservation", "resonance", "potential",
    ],
    "mathematics": [
        "structure", "proof", "limit", "invariant", "topology",
        "recursion", "axiom", "function", "graph", "manifold",
        "constraint", "symmetry group", "transformation", "boundary",
    ],
    "biology": [
        "emergence", "adaptation", "feedback", "signal", "membrane",
        "replication", "selection", "gradient", "regulation", "network",
        "threshold", "homeostasis", "mutation", "expression",
    ],
    "cognition": [
        "pattern", "inference", "attention", "memory", "abstraction",
        "analogy", "model", "prediction", "uncertainty", "category",
        "representation", "context", "salience", "binding",
    ],
    "systems": [
        "pressure", "flow", "bottleneck", "coupling", "oscillation",
        "stability", "attractor", "perturbation", "resilience", "cascade",
        "leverage", "delay", "nonlinearity", "self-organization",
    ],
    "information": [
        "compression", "noise", "channel", "redundancy", "encoding",
        "signal", "bandwidth", "entropy", "mutual information", "error",
        "fidelity", "transmission", "decoding", "capacity",
    ],
}

# Flat list for random sampling
ALL_CONCEPTS = [(concept, domain) for domain, concepts in CONCEPTS.items() for concept in concepts]

# ── Relation type vocabulary ───────────────────────────────────────────────────
# Each relation type changes the structural character of an edge.
# Same node pair, different relation type = different motif.

RELATION_TYPES = [
    "causes",           # A produces B
    "requires",         # A cannot exist without B
    "contradicts",      # A and B cannot coexist at high values
    "emerges_from",     # B is a higher-order property of A
    "constrains",       # A limits the possible states of B
    "amplifies",        # A strengthens the effect of B
    "stabilizes",       # A reduces variance in B
    "destabilizes",     # A increases variance in B
    "analogous_to",     # A and B share structural pattern
    "is_dual_of",       # A and B are complementary perspectives on same structure
]

# Relation weights by type — some relations are structurally stronger
RELATION_WEIGHTS = {
    "causes":        0.9,
    "requires":      0.85,
    "contradicts":   0.8,
    "emerges_from":  0.75,
    "constrains":    0.7,
    "amplifies":     0.65,
    "stabilizes":    0.6,
    "destabilizes":  0.55,
    "analogous_to":  0.5,
    "is_dual_of":    0.5,
}

# Cross-domain relation types — rarer, structurally significant
CROSS_DOMAIN_RELATIONS = [
    "analogous_to",
    "is_dual_of",
    "emerges_from",
]

# Within-domain relation types — more common, form local clusters
WITHIN_DOMAIN_RELATIONS = [
    "causes",
    "requires",
    "constrains",
    "amplifies",
    "stabilizes",
]


# ── Sampling functions ─────────────────────────────────────────────────────────

def sample_concept():
    """Draw a random concept and its domain from the vocabulary."""
    concept, domain = random.choice(ALL_CONCEPTS)
    return concept, domain


def sample_relation(src_domain, dst_domain):
    """
    Draw a relation type appropriate to the domain relationship.

    Cross-domain connections use structurally significant relation types.
    Within-domain connections use tighter, causal relation types.
    """
    if src_domain != dst_domain:
        return random.choice(CROSS_DOMAIN_RELATIONS)
    else:
        return random.choice(WITHIN_DOMAIN_RELATIONS)


def relation_weight(relation_type):
    """Return the structural weight for a given relation type."""
    return RELATION_WEIGHTS.get(relation_type, 0.5)


def semantic_distance(concept_a, domain_a, concept_b, domain_b):
    """
    Compute a rough semantic distance between two concept-domain pairs.

    0.0 = identical
    1.0 = maximally distant

    Currently domain-level only. Phase 3 will introduce embedding-based distance.
    Same domain: low distance (0.1-0.3)
    Different domain: higher distance (0.5-0.9)
    """
    if concept_a == concept_b:
        return 0.0
    if domain_a == domain_b:
        return random.uniform(0.1, 0.35)
    return random.uniform(0.5, 0.9)


def describe_hole_demand(surrounding_domains, surrounding_relations):
    """
    Given the domains and relation types surrounding a hole,
    produce a natural language description of what the hole demands.

    This is the engine beginning to ask questions in language.
    Phase 3 will make this precise. For now it is structural inference
    expressed in approximate terms.
    """
    if not surrounding_domains:
        return "an unknown concept in an uncharted region"

    domain_counts = {}
    for d in surrounding_domains:
        domain_counts[d] = domain_counts.get(d, 0) + 1
    dominant = max(domain_counts, key=domain_counts.get)

    relation_counts = {}
    for r in surrounding_relations:
        relation_counts[r] = relation_counts.get(r, 0) + 1
    dominant_relation = max(relation_counts, key=relation_counts.get) if relation_counts else "related"

    cross_domain = len(domain_counts) > 1
    if cross_domain:
        domains_str = " and ".join(sorted(domain_counts.keys()))
        return (
            f"a concept that bridges {domains_str}, "
            f"primarily {dominant_relation} to its neighbors"
        )
    else:
        return (
            f"a {dominant} concept that {dominant_relation} "
            f"the surrounding structure"
        )


# ── Compatibility aliases ──────────────────────────────────────────────────────
# settler.py and other modules import these names. They are derived from CONCEPTS.

CONCEPT_VOCABULARY = [
    (concept, domain)
    for domain, concepts in CONCEPTS.items()
    for concept in concepts
]

DOMAIN_INDEX = {domain: i for i, domain in enumerate(CONCEPTS.keys())}
