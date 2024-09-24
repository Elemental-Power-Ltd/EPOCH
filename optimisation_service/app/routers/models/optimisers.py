from enum import Enum, StrEnum
from typing import Literal

from pydantic import BaseModel, Field, PositiveFloat, PositiveInt

from app.internal.genetic_algorithm import NSGA2, GeneticAlgorithm, SamplingMethod
from app.internal.grid_search import GridSearch


class OptimiserStr(StrEnum):
    NSGA2 = "NSGA2"
    GeneticAlgorithm = "GeneticAlgorithm"
    GridSearch = "GridSearch"


class OptimiserFunc(Enum):
    NSGA2 = NSGA2
    GeneticAlgorithm = GeneticAlgorithm
    GridSearch = GridSearch


class GABaseHyperParam(BaseModel):
    pop_size: PositiveInt = Field(examples=[256, 512], description="Size of population.", default=256)
    n_offsprings: PositiveInt = Field(
        examples=[256, 512],
        description="Number of offsprings to generate through crossover at each generation."
        + "Can be greater or smaller than initial pop_size",
        default=128,
    )
    sampling_method: SamplingMethod = Field(
        description="Sampling method used to generate initial population.",
        default=SamplingMethod.LHS,
    )
    prob_crossover: PositiveFloat = Field(
        examples=[0.1, 0.5, 0.9], description="Probability of applying crossover between two parents.", default=0.9
    )
    n_crossover: PositiveInt = Field(examples=[1, 2, 3], description="Number of crossover points.", default=1)
    prob_mutation: PositiveFloat = Field(
        examples=[0.1, 0.5, 0.9], description="Probability of applying mutation to each offspring.", default=0.9
    )
    std_scaler: PositiveFloat = Field(
        examples=[0.2], description="Scales the standard deviation of the mutation's normal distribution.", default=0.2
    )
    tol: PositiveFloat = Field(
        examples=[1e-14],
        description="Termination Criterion."
        + "Minimum required improvement of population's best fitness value over a period of generations. Terminates if below.",
        default=1e-14,
    )
    period: PositiveInt = Field(
        examples=[25],
        description="Termination Criterion. Number of passed generations to include when checking for improvement.",
        default=25,
    )
    n_max_gen: PositiveInt = Field(
        examples=[128, 256, 512],
        description="Termination Criterion. Max number of generations before termination.",
        default=int(1e14),
    )
    n_max_evals: PositiveInt = Field(
        examples=[1e6, 1e9],
        description="Termination Criterion. Max number of fitness evaluations (Epoch simulations) before termination.",
        default=int(1e14),
    )


class GeneticAlgorithmHyperParam(GABaseHyperParam):
    k_tournament: PositiveInt = Field(
        examples=[2, 4, 8, 16], description="Number of parents taking part in selection tournament.", default=2
    )


class GridSearchHyperParam(BaseModel):
    keep_degenerate: bool = Field(description="Include or exclude degenerate solutions.", default=False)


class NSGA2Optmiser(BaseModel):
    name: Literal[OptimiserStr.NSGA2]
    hyperparameters: GABaseHyperParam


class GAOptimiser(BaseModel):
    name: Literal[OptimiserStr.GeneticAlgorithm]
    hyperparameters: GeneticAlgorithmHyperParam


class GridSearchOptimiser(BaseModel):
    name: Literal[OptimiserStr.GridSearch]
    hyperparameters: GridSearchHyperParam
