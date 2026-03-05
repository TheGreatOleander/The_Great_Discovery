"""
hole_detector.py — Phase 3
The Great Discovery

Identifies holes precise enough to name. A hole becomes nameable when:
  1. STRUCTURAL PRECISION  — motif pattern around hole is consistent
  2. DOMAIN TENSION        — hole sits between 2+ domains (boundary position)
  3. RELATION DEMAND       — surrounding edges consistently imply a specific role
  4. FORBIDDEN BOUNDARY    — hole is adjacent to forbidden motif territory

When conditions are met above threshold, the hole is surfaced to the questioner.
"""

from collections import Counter

PRECISION_THRESHOLD = 0.55
DOMAIN_TENSION_MIN  = 2


def analyze_hole(conn, src_id, dst_id):
    c = conn.cursor()
    c.execute("SELECT id, concept, domain FROM nodes")
    node_data = {row[0]: {'concept': row[1], 'domain': row[2]} for row in c.fetchall()}
    if src_id not in node_data or dst_id not in node_data:
        return None

    c.execute("SELECT src, dst, relation_type, weight FROM edges")
    all_edges = c.fetchall()
    edge_set  = set((a, b) for (a, b, _, _) in all_edges)

    neighborhood = {src_id, dst_id}
    for (a, b, _, _) in all_edges:
        if a in (src_id, dst_id) or b in (src_id, dst_id):
            neighborhood.add(a); neighborhood.add(b)

    neighborhood_nodes = [node_data[n] for n in neighborhood if n in node_data]
    neighborhood_edges = [(a,b,r,w) for (a,b,r,w) in all_edges if a in neighborhood and b in neighborhood]

    if len(neighborhood_nodes) < 3:
        return None

    domains       = [n['domain'] for n in neighborhood_nodes]
    domain_counts = Counter(domains)
    n_domains     = len(domain_counts)
    if n_domains < DOMAIN_TENSION_MIN:
        return None

    relation_types   = [r for (_,_,r,_) in neighborhood_edges]
    relation_counts  = Counter(relation_types)
    inbound_rels     = [r for (a,b,r,_) in neighborhood_edges if b == src_id]
    outbound_rels    = [r for (a,b,r,_) in neighborhood_edges if a == dst_id]
    dominant_rel     = relation_counts.most_common(1)[0][0] if relation_counts else 'related'

    precision = (relation_counts.most_common(1)[0][1] / len(relation_types)) if relation_types else 0.0
    if precision < PRECISION_THRESHOLD:
        return None

    c.execute("SELECT signature FROM forbidden")
    forbidden_sigs   = set(row[0] for row in c.fetchall())
    forbidden_adj    = len(forbidden_sigs) > 0

    src_node = node_data[src_id]
    dst_node = node_data[dst_id]

    adjacent_concepts = list(set(
        [node_data[b]['concept'] for (a,b,_,_) in all_edges if a==src_id and b in node_data] +
        [node_data[a]['concept'] for (a,b,_,_) in all_edges if b==dst_id and a in node_data]
    ))

    return {
        'src_id': src_id, 'dst_id': dst_id,
        'src_concept': src_node['concept'], 'dst_concept': dst_node['concept'],
        'src_domain': src_node['domain'],   'dst_domain': dst_node['domain'],
        'border_domains': sorted(set([src_node['domain'], dst_node['domain']])),
        'is_cross_domain': src_node['domain'] != dst_node['domain'],
        'adjacent_concepts': adjacent_concepts[:6],
        'dominant_relation': dominant_rel,
        'top_relations': [r for r,_ in relation_counts.most_common(3)],
        'inbound_relations': list(set(inbound_rels)),
        'outbound_relations': list(set(outbound_rels)),
        'precision': precision,
        'n_domains': n_domains,
        'domain_counts': dict(domain_counts),
        'forbidden_adjacent': forbidden_adj,
        'neighborhood_size': len(neighborhood_nodes),
    }


def find_nameable_holes(conn, limit=3):
    c = conn.cursor()
    c.execute("SELECT src, dst FROM edges")
    raw_edges = c.fetchall()
    edge_set  = set(raw_edges)
    if not raw_edges:
        return []

    degree = {}
    for (a,b) in raw_edges:
        degree[a]=degree.get(a,0)+1; degree[b]=degree.get(b,0)+1

    candidates = []
    seen = set()
    for (a,b) in raw_edges:
        for (b2,d) in raw_edges:
            if b==b2 and (a,d) not in edge_set and a!=d:
                key=(min(a,d),max(a,d))
                if key not in seen:
                    seen.add(key)
                    candidates.append((degree.get(a,0)+degree.get(d,0), a, d))

    candidates.sort(reverse=True)
    profiles = []
    for (urgency, a, d) in candidates[:limit*6]:
        p = analyze_hole(conn, a, d)
        if p:
            p['urgency'] = urgency
            profiles.append(p)
        if len(profiles) >= limit:
            break

    profiles.sort(key=lambda p: p['precision'] * p['urgency'], reverse=True)
    return profiles[:limit]
