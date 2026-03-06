
import re

class SymbolicScanner:

    def __init__(self):
        self.patterns = [
            r"loop",
            r"mirror",
            r"paradox",
            r"recursion",
            r"symmetry",
            r"compression"
        ]

    def scan(self, text):

        hits = {}

        for p in self.patterns:
            matches = re.findall(p, text, re.I)
            hits[p] = len(matches)

        return hits
