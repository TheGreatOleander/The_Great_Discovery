
class RecursiveDiscovery:

    def __init__(self, generator, scorer):
        self.generator = generator
        self.scorer = scorer
        self.depth = 0

    def run(self, seed, max_depth=5):

        hypothesis = seed

        while self.depth < max_depth:

            new_h = self.generator.generate(hypothesis)

            score,_ = self.scorer.score(new_h)

            if score > 0.6:
                hypothesis = new_h
                self.depth += 1
            else:
                break

        return hypothesis
