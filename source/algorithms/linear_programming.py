from itertools import chain, combinations

import numpy as np
from cvxopt import matrix, glpk

from .base_algorithm import BaseAlgorithm

float_ = np.float

"""
Linear programming
"""


class LinearProgramming(BaseAlgorithm):

    @staticmethod
    def edges_to_tour(edges):
        tour, current = [], None
        while edges:
            if current:
                for edge in edges:
                    if current not in edge:
                        continue
                    current = edge[0] if current == edge[1] else edge[1]
                    tour.append(current)
                    edges.remove(edge)
            else:
                x, y = edges.pop()
                tour.extend([x, y])
                current = y
        return tour[:-1]

    def ilp_solver(self):
        if self.size > 15:
            print('*** Warning: Linear Programing does not work. Linear programming requires lot of memory!')
            return [], []
        n, sx = self.size, self.size * (self.size - 1) // 2
        c = [float_(self.distances[i + 1][j + 1]) for i in range(n) for j in range(i + 1, n)]
        G, h, A, b = [], [], [], np.full(n, 2, dtype=float_)
        for st in chain.from_iterable(combinations(range(n), r) for r in range(2, n)):
            # !!! it consumes a lot of memory, sum C(n,r),r=2..n => n!/(r!(n-r)!)
            # !!! memory requires nearly O(n!)
            G += [[float_(i in st and j in st) for i in range(n) for j in range(i + 1, n)]]
            h.append(-float_(1 - len(st)))
        for k in range(n):
            A.append([float_(k in (i, j)) for i in range(n) for j in range(i + 1, n)])
        A, G, b, c, h = map(matrix, (A, G, b, c, h))
        _, x = glpk.ilp(c, G.T, h, A.T, b, B=set(range(sx)))
        reverse_mapping = [(i + 1, j + 1) for i in range(n) for j in range(i + 1, n)]
        tour = self.edges_to_tour([reverse_mapping[k] for k in range(sx) if x[k]])
        intermediate_steps = [[]]
        for point in self.format_solution(tour):
            intermediate_steps.append(intermediate_steps[-1] + [point])
        return intermediate_steps[2:], [self.compute_length(tour)] * n
