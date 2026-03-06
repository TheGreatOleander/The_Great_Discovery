
class QuestionDynamics:

    def __init__(self):
        self.frequency = {}

    def register(self, question):
        self.frequency[question] = self.frequency.get(question, 0) + 1

    def attractors(self, threshold=3):
        return [q for q, f in self.frequency.items() if f >= threshold]
