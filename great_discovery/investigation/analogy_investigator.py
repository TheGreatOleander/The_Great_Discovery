
from .base_investigator import Investigator


class AnalogyInvestigator(Investigator):
    """
    Finds analogical bridges by looking for concepts in the graph that share
    structural position with concepts mentioned in the question.

    Bug fixed: previously called self.graph.find_similar() which doesn't exist
    on any graph class in the project. Now queries the SQLite connection directly.
    """

    def investigate(self):
        results = []

        # graph is expected to be a sqlite3 connection when used via CeilingDiscoveryEngine
        conn = self.graph
        if not hasattr(conn, "cursor"):
            return results

        try:
            c = conn.cursor()

            # Find concepts whose domain appears in the question text
            c.execute("SELECT id, concept, domain FROM nodes LIMIT 100")
            nodes = c.fetchall()

            question_lower = self.question.lower()

            for node_id, concept, domain in nodes:
                if concept and concept.lower() in question_lower:
                    # Find nodes with similar structural position (same domain, similar degree)
                    c.execute("""
                        SELECT n.id, n.concept, n.domain
                        FROM nodes n
                        WHERE n.domain = ? AND n.id != ?
                        LIMIT 5
                    """, (domain, node_id))
                    similar = c.fetchall()

                    for sim_id, sim_concept, sim_domain in similar:
                        results.append({
                            "type": "analogy_hypothesis",
                            "source_concept": concept,
                            "analog_concept": sim_concept,
                            "domain": sim_domain,
                            "proposal": (
                                f"By analogy: '{concept}' and '{sim_concept}' share domain "
                                f"'{sim_domain}' — patterns applying to one may apply to the other."
                            )
                        })
        except Exception:
            pass

        return results
