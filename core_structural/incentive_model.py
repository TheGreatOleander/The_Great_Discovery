
import numpy as np

class IncentiveModel:
    def __init__(self):
        self.utilities = {}
        self.global_objective = None

    def set_global_objective(self, func):
        self.global_objective = func

    def add_actor_utility(self, actor, func):
        self.utilities[actor] = func

    def divergence(self, state, epsilon=1e-5):
        if self.global_objective is None:
            return 0.0

        total_divergence = 0.0
        for actor, util in self.utilities.items():
            grad_u = self._numerical_gradient(util, state, epsilon)
            grad_g = self._numerical_gradient(self.global_objective, state, epsilon)
            total_divergence += np.linalg.norm(grad_u - grad_g)
        return total_divergence

    def _numerical_gradient(self, func, state, epsilon):
        grad = []
        for i in range(len(state)):
            state_eps = state.copy()
            state_eps[i] += epsilon
            grad.append((func(state_eps) - func(state)) / epsilon)
        return np.array(grad)
