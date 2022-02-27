import numpy as np

import test_config as config

config.import_context_roots()

from source.commons.tsplib_loader import read_TSP_instance, CannotResolveError
import os
import tsplib95
import pandas as pd

TSP_DATA_PATH = '../../data/tsp'


def test_custom_tsplib_loader():
    """ test custom tsplib parser"""
    info = []
    for name in os.listdir(TSP_DATA_PATH):
        try:
            filepath = os.path.join(TSP_DATA_PATH, name)
            instance = read_TSP_instance(filepath)
            info.append(
                (np.str(instance['INFO']['NAME']), np.int32(instance['INFO']['DIMENSION']),
                 np.True_ if 'NODES' in instance['DATA'] else np.False_))
        except CannotResolveError:
            info.append((np.nan, np.str(name), np.nan))
    df = pd.DataFrame(columns=['name', 'dimension', 'contains_cities'], data=info)
    df.sort_values(['contains_cities', 'dimension'], inplace=True, ascending=[False, True])
    df.to_csv('../../data/tsp_problems.csv' or None, index=False, na_rep='NAN')
    print(df.info())


def test_common_tsplib_loader():
    """ test third-party tsplib95 """
    for name in os.listdir(TSP_DATA_PATH):
        print(name)
        try:
            filepath = os.path.join(TSP_DATA_PATH, name)
            problem = tsplib95.load(filepath)
            G = problem.get_graph()
            print(G.graph)
        except Exception as exc:
            print(exc)


test_custom_tsplib_loader()
