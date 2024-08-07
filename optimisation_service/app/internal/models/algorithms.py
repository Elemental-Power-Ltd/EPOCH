from enum import Enum

from ..genetic_algorithm import NSGA2, GeneticAlgorithm
from ..grid_search import GridSearch


class Optimiser(Enum):
    NSGA2 = NSGA2
    GeneticAlgorithm = GeneticAlgorithm
    GridSearch = GridSearch
