# TSP Algorithms

## Introduction

The travelling salesman problem (TSP) asks the following question: "Given a list of cities and the distances between
each pair of cities, what is the shortest possible route that visits each city and returns to the origin city ?

This Project uses various approaches to solve the TSP (linear programming, construction heuristics, optimization
heuristics, genetic algorithm). It provides a step-by-step visualization of each of these algorithms.

## Get Started

1. Install

   The easiest way to prepare the environment with all required packages is to use conda or pypi.

   conda:
    ```shell
    conda env create -f environment.yml
    ```

   pypi:

    ```shell
    pip install -r requirements.txt
    ```

2. Run Alogorihm

   The tsplib data provided is in the data/TSP.

   Use it like this:
   ```shell
    python tsp.py burma14 -alg ilp_solver
    python tsp.py att48 -alg nearest_neighbor pairwise_exchange ilp_solver genetic
   ```
   See details:
    ```shell
    python tsp.py -h
    ```
