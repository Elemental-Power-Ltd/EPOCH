from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, PositiveFloat, PositiveInt

from app.models.ga_utils import SamplingMethod


class OptimiserStr(StrEnum):
    NSGA2 = "NSGA2"
    GridSearch = "GridSearch"
    Bayesian = "Bayesian"


class NSGA2HyperParam(BaseModel):
    pop_size: PositiveInt = Field(examples=[256], description="Size of population.", default=256)
    n_offsprings: PositiveInt = Field(
        examples=[128],
        description="Number of offsprings to generate through crossover at each generation."
        + "Can be greater or smaller than initial pop_size",
        default=128,
    )
    prob_crossover: PositiveFloat = Field(
        examples=[0.2], description="Probability of applying crossover between two parents.", default=0.2
    )
    n_crossover: PositiveInt = Field(examples=[1, 2], description="Number of crossover points.", default=2)
    prob_mutation: PositiveFloat = Field(
        examples=[0.8], description="Probability of applying mutation to each offspring.", default=0.8
    )
    std_scaler: PositiveFloat = Field(
        examples=[1.0], description="Scales the standard deviation of the mutation's normal distribution.", default=1.0
    )
    tol: PositiveFloat = Field(
        examples=[0.1],
        description="Termination Criterion."
        + "Minimum required improvement of population's best fitness value over a period of generations. Terminates if below.",
        default=0.1,
    )
    period: PositiveInt = Field(
        examples=[50],
        description="Termination Criterion. Number of passed generations to include when checking for improvement.",
        default=50,
    )
    cv_tol: PositiveFloat = Field(
        examples=[0.001],
        description="Termination Criterion."
        + "Minimum required improvement of population's best constraint violation value over a period of generations."
        + "Terminates if below.",
        default=0.001,
    )
    cv_period: PositiveInt = Field(
        examples=[100],
        description="Termination Criterion."
        + "Number of passed generations to include when checking for constraint violation improvement.",
        default=100,
    )
    n_max_gen: PositiveInt = Field(
        examples=[1000, 2000],
        description="Termination Criterion. Max number of generations before termination.",
        default=1000,
    )
    n_max_evals: PositiveInt = Field(
        examples=[1e6, 1e9],
        description="Termination Criterion. Max number of fitness evaluations (Epoch simulations) before termination.",
        default=int(1e14),
    )
    sampling: SamplingMethod = Field(
        examples=["RANDOM", "ESTIMATE"],
        description="Whether to generate initial population randomly or from estimates.",
        default=SamplingMethod.RANDOM,
    )
    pop_size_incr_scalar: PositiveFloat = Field(
        examples=[0.1],
        description="Scalar value to increase the pop_size and n_offsprings by for the next generation when the number of"
        + "optimal scenarios surpasses pop_size_incr_threshold percent of the pop_size.",
        default=0.1,
    )
    pop_size_incr_threshold: PositiveFloat = Field(
        examples=[0.9], description="Percent of the pop_size to set as the threshold to increase the pop_size.", default=0.9
    )
    return_least_infeasible: bool = Field(
        examples=[True, False],
        description="Whether or not to return the most feasible of the infeasible solutions if no feasible solution is found.",
        default=True,
    )


class BayesianHyperParam(BaseModel):
    n_per_sub_portfolio: PositiveInt = Field(examples=[1, 2], description="Number of sites per sub portfolio.", default=1)
    n_generations: PositiveInt = Field(examples=[10, 20], description="Number of generations.", default=10)
    batch_size: PositiveInt = Field(examples=[1, 2, 3, 4], description="Number of evaluations per generation.", default=4)
    n_init_samples: PositiveInt = Field(examples=[5, 10], description="Number of evaluations to initialise model.", default=5)
    num_restarts: PositiveInt = Field(
        examples=[2, 10], description="Number of restarts of the acquisition function optimisation process.", default=10
    )
    raw_samples: PositiveInt = Field(
        examples=[16, 512],
        description="Number of raw samples to initialise acquisition function optimisation process with.",
        default=512,
    )
    mc_samples: PositiveInt = Field(examples=[4, 128], description="Size of samples.", default=128)
    NSGA2_param: NSGA2HyperParam = Field(
        description="Hyperparameters for the NSGA2 algorithm.",
        default=NSGA2HyperParam(pop_size=128, n_offsprings=64),
    )


class GridSearchHyperParam(BaseModel):
    keep_degenerate: bool = Field(description="Include or exclude degenerate solutions.", default=False)


class NSGA2Optmiser(BaseModel):
    name: Literal[OptimiserStr.NSGA2]
    hyperparameters: NSGA2HyperParam


class GridSearchOptimiser(BaseModel):
    name: Literal[OptimiserStr.GridSearch]
    hyperparameters: GridSearchHyperParam


class BayesianOptimiser(BaseModel):
    name: Literal[OptimiserStr.Bayesian]
    hyperparameters: BayesianHyperParam
