
class PatternIndex:

    def __init__(self):
        self.patterns = {}

    def add(self, pattern, solution):
        self.patterns.setdefault(pattern, []).append(solution)

    def match(self, pattern):
        return self.patterns.get(pattern, [])
