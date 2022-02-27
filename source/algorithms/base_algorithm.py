from random import sample

from source.commons import tsplib_loader as loader


class BaseAlgorithm:

    def __init__(self, filepath):
        instance = loader.read_TSP_instance(filepath)
        self.info, self.size, self.cities, self.coords, self.distances = self.load_data(instance)

    @staticmethod
    def load_data(instance):
        info = instance['INFO']
        size = instance['INFO']['DIMENSION']
        cities = list(range(1, size + 1))
        data = instance['DATA']
        if 'NODES' not in data:
            print('*** Warning: Node coordinates are not included in the data')
            coords = dict()
        else:
            coords = data['NODES']
            coords = {c_id: (coords[c_id][0], coords[c_id][1]) for c_id in cities}
        distances = data['EDGES']
        return info, size, cities, coords, distances

    # add node k between node i and node j
    def add(self, i, j, k):
        return self.distances[i][k] + self.distances[k][j] - self.distances[i][j]

    # sample a set of cities (for optimization heuristics)
    def generate_solution(self):
        return sample(self.cities, self.size)

    # computes the total geographical length of a solution
    def compute_length(self, solution):
        total_length = 0
        for i in range(len(solution)):
            length = self.distances[solution[i]][solution[(i + 1) % len(solution)]]
            total_length += length
        return total_length

    def format_solution(self, solution):
        if len(self.coords) == 0:
            return []
        solution = solution + [solution[0]]
        return [self.coords[city] for city in solution]
