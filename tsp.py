"""
A matplotlib-based interactive GUI for showing some tsp algorithms.
TSP Problems:
    see data/tsp/, data/tsp_problems.csv
    see http://dimacs.rutgers.edu/archive/Challenges/TSP/download.html
TSP Algorithms supported:
    - Construction heuristics
        - Nearest neighbor => nearest_neighbor
        - Nearest insertion => nearest_insertion
        - Farthest insertion => farthest_insertion
        - Cheapest insertion => cheapest_insertion
    - Linear programming => ilp_solver
    - Optimization heuristics
        - Pairwise exchange (2-opt) => pairwise_exchange
        - Node insertion => node_insertion
        - Edge insertion => edge_insertion
    - Genetic algorithm => genetic
Usage:
    python tsp.py burma14 -alg ilp_solver
    python tsp.py att48 -alg nearest_neighbor pairwise_exchange ilp_solver genetic
    etc.
See details:
    python tsp.py -h
"""
import argparse
import os.path
import sys

import numpy as np

from source.algorithms.genetic_algorithm import GeneticAlgorithm
from source.algorithms.tsp_algorithms import TSP
from source.commons.plotter import Plotter

APP_NAME = 'TSP ALGORITHMS'
PROBLEMS_DIR = 'data/tsp'


def process_args():
    """
    To parse users' args
    """
    parser = argparse.ArgumentParser(
        description='A matplotlib-based interactive GUI that supports various tsp algorithms '
                    'including {}.'.format(', '.join(TSP.algorithms)))
    parser.add_argument('problem', metavar='TSP Problem',
                        help='specify the tsp problem. see detail in {}'.format(PROBLEMS_DIR))
    parser.add_argument('-alg', '--algorithms', metavar='TSP Algorithms', nargs='*',
                        help='specify the algorithms to be run and demonstrated'
                             '(default, select all)')
    # support for genetic algorithm
    genetic_group = parser.add_argument_group('Genetic Algorithm Specified')
    genetic_group.add_argument('-cr', type=float, metavar='CROSSOVER VALUE', help='crossover value(in range [0, 1])',
                               default=0.5)
    genetic_group.add_argument('-crossover', default='OC',
                               help='crossover method (support: {})'.format(', '.join(GeneticAlgorithm.crossovers)))
    genetic_group.add_argument('-mr', type=float, metavar='MUTATION VALUE', help='mutation value(in range [0, 1])',
                               default=0.5)
    genetic_group.add_argument('-mutation', default='SWAP',
                               help='mutation method (support: {})'.format(', '.join(GeneticAlgorithm.mutations)))
    genetic_group.add_argument('-iter', metavar='ITERATION', type=int, default=100, help='max iteration(default=100)')
    args = parser.parse_args()
    path = os.path.join(PROBLEMS_DIR, args.problem + '.tsp')
    if not os.path.exists(path):
        print('*** Usage error: problem {} is not supported.'.format(args.problem))
        sys.exit(1)
    else:
        args.problem = path
    if not args.algorithms:
        args.algorithms = TSP.algorithms
        print('*** Warning: all algorithms will be run')
    else:
        for alg in args.algorithms:
            if alg not in TSP.algorithms:
                print('*** Usage error: -alg, algorithm {} is not supported.'.format(alg))
                sys.exit(1)
    if args.iter <= 0:
        print('*** Usage error: -iter {} should be positive.'.format(args.iter))
        sys.exit(1)
    if args.crossover.upper() not in GeneticAlgorithm.crossovers:
        print('*** Usage error: -crossover, crossover method {} is not supported.'.format(args.crossover))
        sys.exit(1)
    if args.mutation.upper() not in GeneticAlgorithm.mutations:
        print('*** Usage error: -mutation, mutation method {} is not supported.'.format(args.mutation))
        sys.exit(1)
    if args.cr and (args.cr < 0 or args.cr > 1):
        print('*** Usage error: -cr, crossover value should be in range(0., 1.)'.format(args.cr))
        sys.exit(1)
    if args.mr and (args.mr < 0 or args.mr > 1):
        print('*** Usage error: -mu, mutation value should be in range(0., 1.)'.format(args.mr))
        sys.exit(1)
    return args


def main():
    args = process_args()
    app = Plotter(APP_NAME)
    app.start()
    app.task_done('update_log', 'Loading data')
    tsp = TSP(args.problem)
    app.task_done('update_infos', tsp.info)
    app.task_done('plot_cities', list(tsp.coords.values()))
    for alg in args.algorithms:
        app.task_done('update_log', 'Running algorithm [{}]'.format(alg))
        if alg == 'genetic':
            # genetic algorithm iteration
            generation, best_len = [], np.inf
            for i in range(1, args.iter + 1):
                generation, best, length = tsp.run_algorithm(alg, generation=generation, cr=args.cr,
                                                             crossover=args.crossover, mr=args.mr,
                                                             mutation=args.mutation)
                if length < best_len:
                    best_len = length
                app.task_done('update_log', 'Iter[{}]: Best={:<10.3g}'.format(i, best_len))
                app.task_done('plot_tours', [best], [length], block=True)
        else:
            paths, dists = tsp.run_algorithm(alg)
            app.task_done('update_log', 'Complete algorithm [{}]'.format(alg))
            app.task_done('update_log', 'Start to draw tour\'s path')
            app.task_done('plot_tours', paths, dists, block=True)
            app.task_done('update_log', 'Complete drawing path')
    app.close()


if __name__ == '__main__':
    main()
