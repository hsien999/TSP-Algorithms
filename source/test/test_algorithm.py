import test_config as config

config.import_context_roots()

from source.algorithms.tsp_algorithms import TSP


def test_algorithm():
    """ test algorithms"""
    tsp = TSP('../../data/tsp/burma14.tsp')
    for alg in tsp.algorithms:
        print(alg)
        res = getattr(tsp, alg)()
        for r in res[0]:
            print(r)


def test_performance(problems, algorithms=None):
    pass
