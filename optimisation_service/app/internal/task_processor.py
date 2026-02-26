import asyncio
import datetime
import logging
from concurrent.futures import ThreadPoolExecutor

from app.dependencies import HTTPClient
from app.internal.bayesian.bayesian import Bayesian
from app.internal.bayesian.research import BayesianResearch
from app.internal.database.results import process_results, transmit_results
from app.internal.NSGA2 import NSGA2, SeparatedNSGA2, SeparatedNSGA2xNSGA2
from app.internal.portfolio_simulator import simulate_scenario
from app.internal.queue import IQueue
from app.models.algorithms import Algorithm
from app.models.optimisers import OptimiserStr

logger = logging.getLogger("default")

_ALGORITHM_MAP: dict[OptimiserStr, type[Algorithm]] = {
    OptimiserStr.NSGA2: NSGA2,
    OptimiserStr.SeparatedNSGA2xNSGA2: SeparatedNSGA2xNSGA2,
    OptimiserStr.SeparatedNSGA2: SeparatedNSGA2,
    OptimiserStr.Bayesian: Bayesian,
    OptimiserStr.BayesianResearch: BayesianResearch,
}


async def process_tasks(queue: IQueue, http_client: HTTPClient) -> None:
    """
    Loop to process tasks in queue.

    Parameters
    ----------
    queue
        Asyncio queue containing oustanding optimisation tasks.
    http_client
        Asynchronous HTTP client to use for requests.
    """
    logger.info("Initialising worker loop.")
    while True:
        logger.info("Awaiting next task from queue.")
        task = await queue.get()
        try:
            logger.info(f"Optimising {task.task_id}.")
            loop = asyncio.get_event_loop()
            optimiser = _ALGORITHM_MAP[task.optimiser.name](**dict(task.optimiser.hyperparameters))
            with ThreadPoolExecutor() as executor:
                results = await loop.run_in_executor(
                    executor,
                    lambda: optimiser.run(  # noqa: B023
                        objectives=task.objectives,  # noqa: B023
                        constraints=task.portfolio_constraints,  # noqa: B023
                        portfolio=task.portfolio,  # noqa: B023
                    ),
                )
            logger.info(f"Finished optimising {task.task_id}.")
            completed_at = datetime.datetime.now(datetime.UTC)
            payload = process_results(task.task_id, results, completed_at)
            await transmit_results(results=payload, http_client=http_client)
        except Exception:
            logger.error(f"Exception occured, skipping {task.task_id}.", exc_info=True)
            pass
        simulate_scenario.cache_clear()
        queue.mark_task_done(task)
