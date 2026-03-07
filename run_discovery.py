
import sqlite3
import random
import time

DB="discovery.db"

SEED_CONCEPTS=[
    "mass",
    "field",
    "particle",
    "energy",
    "momentum"
]

def ensure_schema(conn):
    c=conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS nodes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS edges(
        source INTEGER,
        target INTEGER,
        relation_type TEXT DEFAULT 'related',
        weight REAL DEFAULT 1.0
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS semantic_pressure(
        epoch INTEGER PRIMARY KEY,
        structural_compress REAL,
        semantic_compress REAL,
        mismatch REAL,
        value REAL
    )
    """)

    conn.commit()

def seed_nodes(conn):
    c=conn.cursor()
    for n in SEED_CONCEPTS:
        c.execute("INSERT OR IGNORE INTO nodes(name) VALUES(?)",(n,))
    conn.commit()

def get_nodes(conn):
    c=conn.cursor()
    return [r[0] for r in c.execute("SELECT id FROM nodes")]

def add_edge(conn,a,b):
    c=conn.cursor()
    c.execute("INSERT INTO edges(source,target) VALUES(?,?)",(a,b))
    conn.commit()

def edge_count(conn):
    c=conn.cursor()
    return c.execute("SELECT COUNT(*) FROM edges").fetchone()[0]

def node_count(conn):
    c=conn.cursor()
    return c.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]

def detect_holes(conn):
    c=conn.cursor()

    holes=0

    edges=list(c.execute("SELECT source,target FROM edges"))

    for a,b in edges:
        for c1,c2 in edges:
            if b==c1:
                exists=c.execute(
                    "SELECT 1 FROM edges WHERE source=? AND target=?",
                    (a,c2)
                ).fetchone()
                if not exists:
                    holes+=1

    return holes

def spawn_node(conn):
    c=conn.cursor()
    name="concept_"+str(int(time.time()*1000))[-6:]
    c.execute("INSERT INTO nodes(name) VALUES(?)",(name,))
    conn.commit()

def pressure(holes):
    structural=holes*0.1
    semantic=holes*0.2
    mismatch=holes*0.05
    value=structural+semantic+mismatch
    return structural,semantic,mismatch,value

def run(iterations=100):

    conn=sqlite3.connect(DB)

    ensure_schema(conn)
    seed_nodes(conn)

    nodes=get_nodes(conn)

    for i in range(iterations):

        print("----------------")
        print("iteration",i)

        nodes=get_nodes(conn)

        a=random.choice(nodes)
        b=random.choice(nodes)

        if a!=b:
            add_edge(conn,a,b)

        holes=detect_holes(conn)

        if holes>3:
            spawn_node(conn)

        sc,sem,mis,val=pressure(holes)

        conn.execute(
            "INSERT OR REPLACE INTO semantic_pressure VALUES(?,?,?,?,?)",
            (i,sc,sem,mis,val)
        )
        conn.commit()

        print("nodes:",node_count(conn))
        print("edges:",edge_count(conn))
        print("holes detected:",holes)

    print()
    print("Discovery run complete.")

if __name__=="__main__":
    run()
