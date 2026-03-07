"""
Discovery Driver

Runs a discovery epoch and evolves the concept graph.
"""

import random
from great_discovery.core_engine import init_db


# ---------- Graph Operations ----------

def seed_nodes(conn):

    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM nodes")
    count = cur.fetchone()[0]

    if count == 0:

        seeds = [
            ("number", "math"),
            ("force", "physics"),
            ("cell", "biology"),
            ("symbol", "language"),
            ("energy", "physics")
        ]

        for concept, domain in seeds:
            cur.execute(
                """
                INSERT INTO nodes(concept, domain, introduced)
                VALUES (?, ?, 0)
                """,
                (concept, domain)
            )

        conn.commit()


def grow_graph(conn, epoch):

    cur = conn.cursor()

    cur.execute("SELECT id FROM nodes")
    nodes = [r[0] for r in cur.fetchall()]

    if len(nodes) < 2:
        return

    a, b = random.sample(nodes, 2)

    cur.execute(
        """
        INSERT INTO edges(source, target)
        VALUES (?, ?)
        """,
        (a, b)
    )

    conn.commit()


def detect_holes(conn):

    cur = conn.cursor()

    query = """
    SELECT id FROM nodes
    WHERE id NOT IN (
        SELECT source FROM edges
        UNION
        SELECT target FROM edges
    )
    """

    cur.execute(query)
    holes = cur.fetchall()

    for h in holes:

        cur.execute(
            "INSERT INTO holes(node_id) VALUES (?)",
            (h[0],)
        )

    conn.commit()

    return len(holes)


def apply_semantic_pressure(conn, holes):

    cur = conn.cursor()

    pressure = random.random() + holes

    cur.execute(
        """
        INSERT INTO semantic_pressure(value)
        VALUES (?)
        """,
        (pressure,)
    )

    conn.commit()


# ---------- Epoch Execution ----------

def run_epoch(epoch_number):

    conn = init_db()

    print("----------------")
    print(f"iteration {epoch_number}")

    try:

        seed_nodes(conn)

        grow_graph(conn, epoch_number)

        holes = detect_holes(conn)

        apply_semantic_pressure(conn, holes)

        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM nodes")
        nodes = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM edges")
        edges = cur.fetchone()[0]

        print("nodes:", nodes)
        print("edges:", edges)
        print("holes detected:", holes)

    except Exception as e:
        print("epoch error:", e)

    finally:
        conn.close()