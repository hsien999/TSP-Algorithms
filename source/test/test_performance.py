import test_config as config

config.import_context_roots()
import os.path
import time

import numpy as np
import pandas as pd

from source.algorithms.genetic_algorithm import GeneticAlgorithm

from source.algorithms.tsp_algorithms import TSP
import matplotlib.pyplot as plt

colors = {alg: f'C{idx}' for idx, alg in enumerate(TSP.algorithms)}


def test_performance(problems):
    """ test algorithms performance"""
    os.makedirs('result', exist_ok=True)
    result = []
    repeat = 1
    for pro in problems:
        path = os.path.join('../../data/tsp/', pro + '.tsp')
        tsp = TSP(path)
        for alg in tsp.algorithms:
            print(pro, alg)
            if alg == 'ilp_solver':
                continue
            if alg == 'genetic':
                generation, best_len = [], np.inf
                for _ in range(100):
                    generation, best, length = tsp.run_algorithm(alg, generation=generation, cr=0.5,
                                                                 crossover='OC', mr=0.5, mutation='SWAP')
                    if length < best_len:
                        best_len = length
                result.append((pro, alg, '{:.1f}'.format(best_len), 0.0))
            else:
                avg_dist, avg_time = 0, 0
                for _ in range(repeat):
                    s0 = time.perf_counter()
                    _, dists = tsp.run_algorithm(alg)
                    elapse = time.perf_counter() - s0
                    avg_dist += dists[-1]
                    avg_time += elapse
                result.append((pro, alg, '{:.1f}'.format(avg_dist / repeat),
                               '{:.3g}'.format(avg_time / repeat)))
    pd.DataFrame(result, columns=('problem', 'algorithm', 'dist', 'time')).to_csv('result/result.csv', index=False)


def test_performance_genetic(problems):
    """ test algorithms performance"""
    os.makedirs('result', exist_ok=True)
    result = []
    for pro in problems:
        path = os.path.join('../../data/tsp/', pro + '.tsp')
        tsp = TSP(path)
        for alg in tsp.algorithms:
            if alg != 'genetic':
                continue
            crossovers, mutations = GeneticAlgorithm.crossovers, GeneticAlgorithm.mutations
            crs, mrs = np.linspace(0.2, 0.8, 3), np.linspace(0.2, 0.8, 3)
            from itertools import product
            for cro, cr, mut, mr in product(crossovers, crs, mutations, mrs):
                print(pro, cro, cr, mut, mr)
                generation, best_len = [], np.inf
                for _ in range(100):
                    generation, best, length = tsp.run_algorithm(alg, generation=generation, cr=cr,
                                                                 crossover=cro, mr=mr, mutation=mut)
                    if length < best_len:
                        best_len = length
                result.append((pro, cro, cr, mut, mr, '{:.1f}'.format(best_len)))
    pd.DataFrame(result, columns=('problem', 'crossovers', 'cr', 'mutations', 'mr' 'dist')) \
        .to_csv('result/result_genetic.csv', index=False)


def plot_bars(col):
    os.makedirs('result', exist_ok=True)
    df = pd.read_csv('result/result.csv', index_col=None, usecols=('problem', 'algorithm', 'dist', 'time'))
    problems = df['problem'].drop_duplicates()
    alg_groups = df.groupby('algorithm')
    group_bars, groups_num = len(alg_groups.groups), len(problems)
    group_width, bar_width = 1.0, 0.8 / group_bars
    x_index = np.arange(groups_num)
    plt.title(f"Comparison of TSP algorithms' {'length' if col == 'dist' else 'time'}")
    plt.xticks(ticks=x_index, labels=problems)
    x_index = x_index - (group_width - bar_width) / 2
    for idx, (alg, table) in enumerate(alg_groups):
        if (table[col] == 0).all():
            continue
        plt.bar(x_index + bar_width * idx, table[col], width=bar_width, label=alg, fc=colors[alg])
    plt.legend(prop={'size': 8})
    plt.savefig(f'result/{col}.png')
    plt.show()


if __name__ == '__main__':
    test_performance(('eil51', 'kroA100', 'kroA200'))
    # plot_bars('dist')
    # plot_bars('time')
