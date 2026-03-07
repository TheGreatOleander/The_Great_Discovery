
class Investigator:
    """Base class for all investigators."""

    def __init__(self, graph, question):
        self.graph = graph
        self.question = question

    def investigate(self):
        raise NotImplementedError("Investigators must implement investigate()")
