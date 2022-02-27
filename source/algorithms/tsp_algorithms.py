from .genetic_algorithm import GeneticAlgorithm
from .linear_programming import LinearProgramming
from .tour_construction import TourConstructionHeuristics


class TSP(GeneticAlgorithm, LinearProgramming, TourConstructionHeuristics):

    def __init__(self, filepath):
        super().__init__(filepath)

    algorithms = (
        # --- construction heuristic method(TourConstructionHeuristics)
        'nearest_neighbor',
        'nearest_insertion',
        'farthest_insertion',
        'cheapest_insertion',
        # --- optimization heuristics method(LocalOptimizationHeuristics)
        'pairwise_exchange',
        'node_insertion',
        'edge_insertion',
        # --- linear method(LinearProgramming)
        'ilp_solver',
        # genetic algorithm (GeneticAlgorithm)
        'genetic'
    )

    def run_algorithm(self, alg, **kwargs):
        if alg not in self.algorithms:
            raise ValueError('Algorithm {!r} is not supported'.format(alg))
        return getattr(self, alg)(**kwargs) if len(kwargs) > 0 else getattr(self, alg)()
