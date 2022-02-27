import math
from collections import defaultdict

import numpy as np
from scipy.spatial.distance import squareform, pdist

"""
This file contains functions to read TSP instances in some of the
formats used in TSPLIB.  All formats currently used in TSPLIB TSP
instances with more than 1000 cities are supported, including

2-D Euclidean instances:  
    EDGE_WEIGHT_TYPE = EUC_2D
    2-D Euclidean instances with ceilings used in distance

calculations:  
    EDGE_WEIGHT_TYPE = CEIL_2D
    
geographic dist:  
    EDGE_WEIGHT_TYPE = GEO
    
Upper triangular distance matrices (including the diagonal):
    EDGE_WEIGHT_TYPE = EXPLICIT, 
    EDGE_WEIGHT_FORMAT = FULL_MATRIX, UPPER_DIAG_ROW, LOWER_DIAG_ROW, UPPER_ROW, LOWER_ROW

!!! NOTE: 
1. The parsing methods provided are still limited and cannot be handled correctly 
while encountering complex problems or large data volumes.
2. We ignore some important problem assumptions
eg. `FIXED_EDGES_SECTION`
3. we assume that `EDGE_DATA_FORMAT` = EDGE_LIST(default)
ie. We only accept fully connected graphs
"""
float_ = np.float32
line_no_ = 0
MAX_NODES = 20000


# ====================================================================
# BACKEND
# ====================================================================
class CannotResolveError(Exception):
    def __init__(self, msg):
        self.error_msg = 'LINE[{}] {}'.format(line_no_, msg)


def __get_text(source):
    splits = source.split(':')
    if len(splits) < 2:
        return None
    return splits[1].strip()


def __hav(angle):
    return math.sin(angle / 2) ** 2


def _haversine_distance(cityA, cityB):
    coords = (*cityA, *cityB)
    # we convert from decimal degree to radians
    lat_cityA, lon_cityA, lat_cityB, lon_cityB = map(math.radians, coords)
    delta_lon = lon_cityB - lon_cityA
    delta_lat = lat_cityB - lat_cityA
    a = __hav(delta_lat) + math.cos(lat_cityA) * math.cos(lat_cityB) * __hav(delta_lon)
    c = 2 * math.asin(math.sqrt(a))
    # approximate radius of the Earth: 6371 km
    return c * 6371


def __read_line(fd):
    global line_no_
    line_no_ += 1
    return fd.readline().strip()


def _read_node_coord_section(edge_weight_type, n_cities, fd):
    if not edge_weight_type or edge_weight_type not in ('EUC_2D', 'CEIL_2D', 'GEO', 'ATT'):
        raise CannotResolveError('Unsupported node coordinates with type {}'.format(edge_weight_type))
    if not n_cities:
        raise CannotResolveError('Unknown dimension of edges: {}'.format(n_cities))
    cities = _fetch_cities_coords(n_cities, fd)
    dist_mat = np.zeros((n_cities + 1, n_cities + 1), dtype=float_)
    if edge_weight_type == 'GEO':
        for idx1 in range(1, n_cities + 1):
            for idx2 in range(1, n_cities + 1):
                dist_mat[idx1][idx2] = dist_mat[idx2][idx1] = \
                    _haversine_distance(cities[idx1], cities[idx2])
    else:
        # pdlist: returns a condensed distance matrix (default = 'euclidean')
        # squareform: covert the condensed distance matrix to redundant one
        dist_mat = squareform(pdist(cities).astype(float_))
        if edge_weight_type == 'ATT':
            dist_mat = np.round_(dist_mat)
    return cities, dist_mat


def _read_edge_weight_section(edge_weight_format, n_cities, fd):
    if not n_cities:
        raise CannotResolveError('Unknown dimension of graph: {}'.format(n_cities))
    if edge_weight_format == 'FULL_MATRIX':
        def row_num(_i):
            return range(n_cities)
    elif edge_weight_format == 'LOWER_DIAG_ROW':
        def row_num(_i):
            return range(_i + 1)
    elif edge_weight_format == 'UPPER_DIAG_ROW':
        def row_num(_i):
            return range(_i, n_cities)
    elif edge_weight_format == 'UPPER_ROW':
        def row_num(_i):
            return range(_i + 1, n_cities)
    elif edge_weight_format == 'LOWER_ROW':
        def row_num(_i):
            return range(_i)
    else:
        raise CannotResolveError('Unsupported edge weight with format {}'.format(edge_weight_format))
    dist_mat = np.empty((n_cities + 1, n_cities + 1), dtype=float_)
    splits, num_idx, num_tol = None, -1, 0
    try:
        for i in range(n_cities):
            for j in row_num(i):
                num_idx += 1
                if num_idx == num_tol:
                    splits = __read_line(fd).split()
                    num_tol = len(splits)
                    num_idx = 0
                    if num_tol == 0:
                        raise CannotResolveError('Data from edge weight section is incomplete')
                val = float_(splits[num_idx])
                dist_mat[i + 1][j + 1] = dist_mat[j + 1][i + 1] = val
    except ValueError:
        raise CannotResolveError('Data from edge weight section contains non-number text')
    return dist_mat


def _fetch_cities_coords(n_cities, fd):
    cities = np.empty((n_cities + 1, 2), dtype=float_)
    try:
        for i in range(n_cities):
            splits = __read_line(fd).split()
            if len(splits) != 3:
                raise CannotResolveError('Unexpected data format in node coordinates(or display data) section')
            city_id, coord1, coord2 = splits
            city_id = int(city_id)
            if city_id < 1 or city_id > n_cities:
                raise CannotResolveError(
                    'Unexpected city id (out of range) in node coordinates(or display data) section')
            cities[city_id][0] = float_(coord1)
            cities[city_id][1] = float_(coord2)
    except ValueError:
        raise CannotResolveError('Data from node coordinates(or display data) section contains non-number text')
    return cities


# ====================================================================
# API
# ====================================================================
def read_TSP_instance(filepath):
    """
    Return a dictionary with info and data of tsp file.
    ----------
    Parameters:
        filepath: read a tsp file from filepath
    ----------
    Returns:
        instance: a tsp instance.
        eg.
            use instance['INFO'] and info keyword(upper) to get the name of a field
            use instance['DATA']['EDGES'] to get the weighted matrix(ndarray)
    """
    global line_no_
    instance = defaultdict(dict)
    n_cities = None
    edge_weight_type = None
    edge_weight_format = None
    fix_edges = False
    line_no_ = 0
    with open(filepath, 'rt') as fd:
        line = __read_line(fd)
        while line:
            line = line.strip()
            if not line:
                break
            # to step over `FIXED_EDGES_SECTION`
            if fix_edges:
                if line == '-1':
                    fix_edges = False
                line = __read_line(fd)
                continue
            # print('line=' + line)
            text = __get_text(line)
            # ------ common attributes
            if line.startswith('NAME'):
                if text.endswith('.tsp'):
                    text = text[:text.index('.tsp')]
                instance['INFO']['NAME'] = text
            elif line.startswith('TYPE'):
                if not text.startswith('TSP'):
                    raise CannotResolveError('This message has type {}, not TSP'.format(text))
                instance['INFO']['TYPE'] = text
            elif line.startswith('COMMENT'):
                instance['INFO']['COMMENT'] = text
            elif line.startswith('DIMENSION'):
                n_cities = int(text)
                if n_cities > MAX_NODES:
                    raise CannotResolveError(
                        'The total number of city nodes({}) is too large(max={})'.format(n_cities, MAX_NODES))
                instance['INFO']['DIMENSION'] = n_cities
            elif line.startswith('EDGE_WEIGHT_TYPE'):
                #
                edge_weight_type = text
                instance['INFO']['EDGE_WEIGHT_TYPE'] = edge_weight_type
            elif line.startswith('EDGE_WEIGHT_FORMAT'):
                edge_weight_format = text
                instance['INFO']['EDGE_WEIGHT_FORMAT'] = edge_weight_format
            # ------ unusual attributes
            elif line.startswith('EDGE_DATA_FORMAT'):
                # EDGE_LIST(default) ADJ_LIST
                if text != 'EDGE_LIST':
                    raise CannotResolveError('Only support `EDGE_LIST` option')
                instance['INFO']['EDGE_DATA_FORMAT'] = text
            elif line.startswith('NODE_COORD_TYPE'):
                # TWOD_COORDS(default) THREED_COORDS NO_COORDS
                instance['INFO']['NODE_COORD_TYPE'] = text
            elif line.startswith('DISPLAY_DATA_TYPE'):
                # COORD_DISPLAY(default) TWOD_DISPLAY NO_DISPLAY
                instance['INFO']['DISPLAY_DATA_TYPE'] = text
            elif line.startswith('FIXED_EDGES_SECTION'):
                # The listed edges are required to appear in each solution of the problem
                # Note: we ignore some data assumptions
                instance['INFO']['FIXED_EDGES_SECTION'] = text
                fix_edges = True
            # ------ edges amd nodes data
            elif line.startswith('EDGE_WEIGHT_SECTION'):
                dist_mat = _read_edge_weight_section(edge_weight_format, n_cities, fd)
                instance['DATA']['EDGES'] = dist_mat
            elif line.startswith('NODE_COORD_SECTION'):
                cities, dist_mat = _read_node_coord_section(edge_weight_type, n_cities, fd)
                instance['DATA']['NODES'] = cities
                instance['DATA']['EDGES'] = dist_mat
            elif line.startswith('DISPLAY_DATA_SECTION'):
                instance['DATA']['NODES'] = _fetch_cities_coords(n_cities, fd)
            elif line.startswith('EOF'):
                break
            else:
                raise CannotResolveError('Unexpected input: {}'.format(line_no_, line))
            line = __read_line(fd)
    return instance
