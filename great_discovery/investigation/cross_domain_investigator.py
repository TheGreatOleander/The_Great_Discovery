
from .base_investigator import Investigator


class CrossDomainInvestigator(Investigator):
    """
    Probes for cross-domain connections by identifying underconnected domain pairs
    relevant to the question.

    Bug fixed: previously accessed self.graph.domains which doesn't exist on any
    graph class in the project. Now queries the SQLite connection directly.
    """

    def investigate(self):
        proposals = []

        conn = self.graph
        if not hasattr(conn, "cursor"):
            return proposals

        try:
            c = conn.cursor()

            # Get the distinct domains present in the graph
            c.execute("SELECT DISTINCT domain FROM nodes WHERE domain IS NOT NULL")
            domains = [row[0] for row in c.fetchall() if row[0] != "recursion"]

            # Find domain pairs that have few edges between them (cross-domain gaps)
            for i in range(len(domains)):
                for j in range(i + 1, len(domains)):
                    d_a, d_b = domains[i], domains[j]

                    c.execute("""
                        SELECT COUNT(*) FROM edges e
                        JOIN nodes n1 ON e.src = n1.id
                        JOIN nodes n2 ON e.dst = n2.id
                        WHERE n1.domain = ? AND n2.domain = ?
                    """, (d_a, d_b))
                    cross_count = c.fetchone()[0]

                    if cross_count < 3:
                        proposals.append({
                            "type": "cross_domain_probe",
                            "domain_a": d_a,
                            "domain_b": d_b,
                            "cross_edges": cross_count,
                            "proposal": (
                                f"Weak bridge between '{d_a}' and '{d_b}' "
                                f"({cross_count} edges) — may relate to: {self.question}"
                            )
                        })
        except Exception:
            pass

        return proposals
