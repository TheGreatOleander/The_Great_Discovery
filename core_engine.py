"""
core_engine.py — Phase 2
The Great Discovery

Phase 2 database schema: nodes and edges are no longer anonymous.

Nodes carry:
  concept     — a meaning anchor (string from the concept vocabulary)
  domain      — the broad field this concept belongs to
  introduced  — epoch when this node entered the graph

Edges carry:
  relation_type — the nature of the connection (causes, requires, contradicts, etc.)
  weight        — strength of the relationship (0.0 to 1.0)

New tables:
  semantic_pressure — per-epoch record of structural vs semantic compression mismatch
  holes             — named holes: regions where the engine has detected a
                      structurally demanded but semantically unfilled position

This is the abstraction layer the engine was always pointing toward.
Topology now carries meaning. Meaning now exerts structural pressure.
"""

import sqlite3


def init_db(path="discovery.db"):
    conn = sqlite3.connect(path)
    c = conn.cursor()

    # Phase 2: nodes carry meaning
    c.execute("""
        CREATE TABLE IF NOT EXISTS nodes (
            id          INTEGER PRIMARY KEY,
            concept     TEXT    DEFAULT 'unknown',
            domain      TEXT    DEFAULT 'unassigned',
            introduced  INTEGER DEFAULT 0
        )
    """)

    # Phase 2: edges carry relationship type and weight
    c.execute("""
        CREATE TABLE IF NOT EXISTS edges (
            src           INTEGER,
            dst           INTEGER,
            relation_type TEXT    DEFAULT 'related',
            weight        REAL    DEFAULT 1.0
        )
    """)

    # Motifs — structural patterns (unchanged)
    c.execute("""
        CREATE TABLE IF NOT EXISTS motifs (
            signature       TEXT PRIMARY KEY,
            count           INTEGER,
            last_seen_epoch INTEGER
        )
    """)

    # Forbidden motifs — edges of the table (unchanged)
    c.execute("""
        CREATE TABLE IF NOT EXISTS forbidden (
            signature   TEXT PRIMARY KEY,
            spike_score REAL
        )
    """)

    # Phase 2: semantic pressure tracking
    # Records the gap between structural and semantic coherence each epoch
    c.execute("""
        CREATE TABLE IF NOT EXISTS semantic_pressure (
            epoch               INTEGER PRIMARY KEY,
            structural_compress REAL,
            semantic_compress   REAL,
            mismatch            REAL
        )
    """)

    # Phase 2: named holes
    # When a hole's shape becomes precise enough, it is surfaced here
    # with its structural signature and a description of what it demands
    c.execute("""
        CREATE TABLE IF NOT EXISTS holes (
            id          INTEGER PRIMARY KEY,
            epoch_found INTEGER,
            shape_sig   TEXT,
            demands     TEXT,
            filled      INTEGER DEFAULT 0,
            filled_by   TEXT    DEFAULT NULL
        )
    """)

    conn.commit()
    return conn
