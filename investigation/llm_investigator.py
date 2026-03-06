
from .base_investigator import Investigator

class LLMInvestigator(Investigator):

    def __init__(self, graph, question, llm):
        super().__init__(graph, question)
        self.llm = llm

    def investigate(self):
        prompt = f"Suggest a concept that could answer: {self.question}"
        response = self.llm.complete(prompt)

        return [{
            "type": "llm_hypothesis",
            "proposal": response
        }]
