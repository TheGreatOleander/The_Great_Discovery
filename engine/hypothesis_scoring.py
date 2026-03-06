
class HypothesisScorer:

    def __init__(self):
        self.weights = {
            "novelty": 0.25,
            "coherence": 0.25,
            "compressibility": 0.25,
            "generativity": 0.25
        }

    def score(self, hypothesis):
        scores = {
            "novelty": self._novelty(hypothesis),
            "coherence": self._coherence(hypothesis),
            "compressibility": self._compressibility(hypothesis),
            "generativity": self._generativity(hypothesis)
        }

        total = 0
        for k,v in scores.items():
            total += v * self.weights[k]

        return total, scores

    def _novelty(self, h):
        return min(len(set(h.split()))/50,1)

    def _coherence(self, h):
        return min(len(h)/500,1)

    def _compressibility(self, h):
        return 1 - (len(set(h))/max(len(h),1))

    def _generativity(self, h):
        return min(h.count("->")/5,1)
