"""
investigation/llm_investigator.py
The Great Discovery

LLM-powered investigator. Given a hole profile and a question the structural
engine generated, asks the LLM for a concrete concept that could fill the gap.

The prompt is built from the full structural context -- source/destination
concepts, domains, relation types, adjacent concepts, and the question itself.
This gives the LLM enough to reason about the specific gap rather than
answering generically.

The response is parsed for a concept name and domain, then returned as a
hypothesis dict the driver loop can log and optionally settle into the graph.
"""

from .base_investigator import Investigator


SYSTEM_CONTEXT = """You are a structural knowledge investigator for an autonomous discovery engine.
The engine has detected a gap in a knowledge graph and generated a research question about it.
Your job is to suggest the single best concept that fills the structural hole.

Respond in this exact format (nothing else):
CONCEPT: <concept name, 2-5 words>
DOMAIN: <one of: physics, mathematics, biology, cognition, systems, information>
REASON: <one sentence explaining why this concept fills the gap>

Be precise. The concept should be something real and nameable, not a description."""


def _build_prompt(question, profile):
    """
    Build a context-rich prompt from the hole profile and question.
    """
    src     = profile.get("src_concept", "unknown")
    dst     = profile.get("dst_concept", "unknown")
    src_dom = profile.get("src_domain",  "unknown")
    dst_dom = profile.get("dst_domain",  "unknown")
    rel     = profile.get("dominant_relation", "relates to")
    adj     = profile.get("adjacent_concepts", [])
    htype   = profile.get("hole_type", "structural")
    cross   = profile.get("is_cross_domain", False)

    adj_str = ", ".join(f"'{c}'" for c in adj[:4]) if adj else "none identified"
    cross_str = f"This is a cross-domain gap between {src_dom} and {dst_dom}." if cross else \
                f"This gap is within the {src_dom} domain."

    return f"""{SYSTEM_CONTEXT}

--- STRUCTURAL CONTEXT ---
Gap type: {htype}
Source concept: '{src}' (domain: {src_dom})
Destination concept: '{dst}' (domain: {dst_dom})
Dominant relation: {rel}
Adjacent concepts in the graph: {adj_str}
{cross_str}

--- RESEARCH QUESTION ---
{question}

--- YOUR TASK ---
What single concept best fills this structural gap?"""


def _parse_response(text):
    """
    Parse CONCEPT / DOMAIN / REASON from LLM response.
    Returns dict or None if parsing fails.
    """
    if not text:
        return None

    concept = None
    domain  = None
    reason  = None

    for line in text.strip().splitlines():
        line = line.strip()
        if line.upper().startswith("CONCEPT:"):
            concept = line.split(":", 1)[1].strip().lower()
        elif line.upper().startswith("DOMAIN:"):
            domain = line.split(":", 1)[1].strip().lower()
        elif line.upper().startswith("REASON:"):
            reason = line.split(":", 1)[1].strip()

    valid_domains = {"physics", "mathematics", "biology", "cognition", "systems", "information"}
    if domain not in valid_domains:
        domain = "cognition"  # safe fallback

    if not concept:
        return None

    return {
        "concept": concept,
        "domain":  domain,
        "reason":  reason or "",
    }


class LLMInvestigator(Investigator):
    """
    Investigates a structural hole by asking the LLM for a concrete concept.

    Constructor:
        graph    : sqlite3 connection (passed through from driver)
        question : str — the research question from questioner.py
        llm      : LLMProvider instance (e.g. AnthropicProvider)
        profile  : dict — hole profile from find_nameable_holes() (optional but recommended)
    """

    def __init__(self, graph, question, llm, profile=None):
        super().__init__(graph, question)
        self.llm     = llm
        self.profile = profile or {}

    def investigate(self):
        prompt   = _build_prompt(self.question, self.profile)
        response = self.llm.complete(prompt)
        parsed   = _parse_response(response)

        if not parsed:
            return []

        src_id = self.profile.get("src_id")
        dst_id = self.profile.get("dst_id")

        return [{
            "type":        "llm_hypothesis",
            "concept":     parsed["concept"],
            "domain":      parsed["domain"],
            "reason":      parsed["reason"],
            "question":    self.question,
            "src_id":      src_id,
            "dst_id":      dst_id,
            "src_concept": self.profile.get("src_concept"),
            "dst_concept": self.profile.get("dst_concept"),
            "raw":         response,
        }]
