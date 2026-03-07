Sidecar System

Sidecars allow domain knowledge to be added without modifying the core engine.

Each sidecar is a small module describing a domain such as:
- math
- physics
- geometry

Structure:

sidecars/
    math/
        concepts.json
        relations.json
    physics/
        concepts.json
        relations.json

The engine can load these dynamically at startup.

Concept example:
{
  "concept": "group",
  "domain": "math",
  "description": "A set with an associative operation, identity, and inverse."
}

Relation example:
{
  "source": "group",
  "target": "symmetry",
  "type": "models"
}