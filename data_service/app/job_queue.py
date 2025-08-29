"""Job queue for background tasks, including dataset generation."""

import asyncio
import json
import typing
from asyncio import Queue
from collections.abc import Awaitable, Callable
from concurrent.futures import ThreadPoolExecutor
from logging import getLogger
from typing import Any

from fastapi import Depends
from httpx import AsyncClient

from app.epl_secrets import SecretDict
from app.internal.elec_meters import VAE
from app.internal.epl_typing import db_pool_t
from app.models.carbon_intensity import GridCO2Request
from app.models.electricity_load import ElectricalLoadRequest
from app.models.heating_load import HeatingLoadRequest
from app.models.import_tariffs import TariffRequest
from app.models.renewables import RenewablesRequest, RenewablesWindRequest
from app.routers.carbon_intensity import generate_grid_co2
from app.routers.electricity_load import generate_electricity_load
from app.routers.heating_load import generate_heating_load
from app.routers.import_tariffs import generate_import_tariffs
from app.routers.renewables import generate_renewables_generation, generate_wind_generation


class TerminateTaskGroup(Exception):
    """Exception raised to terminate a task group."""


class ASyncFunctionRequest[**P, R]:
    """
    Generic job queue function for an async piece of work you want done.

    This is mostly useful for testing or little bits of work that aren't formal endpoints yet.

    Type Parameters
    ---------------
    **P
        Parameters for the function, including args and kwargs
    R
        Return type of the function
    """

    def __init__(self, func: Callable[P, Awaitable[R]], *args: P.args, **kwargs: P.kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def model_dump_json(self) -> str:
        """
        Mimic the pydantic model dumping to a JSON string.

        This returns a JSON representation of the callable, not guaranteed to be round-trippable.

        Parameters
        ----------
        self

        Returns
        -------
        str
            JSON encoded string with keys 'func', 'args' and 'kwargs'
        """
        return json.dumps({"func": repr(self.func), "args": self.args, "kwargs": self.kwargs}, sort_keys=True, default=str)


class SyncFunctionRequest[**P, R]:
    """
    Generic job queue function for a synchronous piece of work you want done.

    This is mostly useful for testing, or for running expensive but time insensitive code in the background.

    Type Parameters
    ---------------
    **P
        Parameters for the function, including args and kwargs
    R
        Return type of the function
    """

    def __init__(self, func: Callable[P, R], *args: P.args, **kwargs: P.kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def model_dump_json(self) -> str:
        """
        Mimic the pydantic model dumping to a JSON string.

        This returns a JSON representation of the callable, not guaranteed to be round-trippable.

        Parameters
        ----------
        self

        Returns
        -------
        str
            JSON encoded string with keys 'func', 'args' and 'kwargs'
        """
        return json.dumps({"func": repr(self.func), "args": self.args, "kwargs": self.kwargs}, sort_keys=True, default=str)


type GenericJobRequest = (
    ASyncFunctionRequest
    | ElectricalLoadRequest
    | GridCO2Request
    | HeatingLoadRequest
    | RenewablesRequest
    | RenewablesWindRequest
    | SyncFunctionRequest
    | TariffRequest
)
from typing import Iterable
type PrepochJobQueueT = Queue[GenericJobRequest]

def is_bundle_in_queue(bundle_id: bundle_id_t, queue: PrepochJobQueueT) -> bool:
    """
    Check if there are any remaining jobs with this bundle ID in the queue.

    This might fire repeatedly if there are multiple workers 

    Parameters
    ----------
    bundle_id
        The ID of the bundle to check for

    Returns
    -------
    bool
        True if there are no other jobs with this bundle ID in the queue
        False if there are remaining jobs.
    """
    # This is accessing a private attribute
    internal_queue: Iterable[GenericJobRequest] = queue._queue
    return any(hasattr(item, "bundle_metadata") and item.bundle_metadata.bundle_id == bundle_id
               for item in internal_queue)

async def process_jobs(
    queue: PrepochJobQueueT,
    pool: db_pool_t,
    http_client: AsyncClient,
    vae: VAE,
    secrets_env: SecretDict,
    ignore_exceptions: bool = False,
) -> None:
    """
    Process all the entries in the queue.

    This is a long running background task that you should start as part of a TaskGroup:
    ```
    async with asyncio.TaskGroup() as tg:
        _ = tg.create_task(
            process_jobs(
                queue,
                ...
            )
        )
        # ... do some work
        await queue.join()
        raise TerminateTaskGroup()  # end th equeue
    ```
    This is an awkward structure, but means that exceptions will be handled correctly.
    You may have multiple workers of this type which will grant small speed benefits if
    your workload is very async-y.

    We decide what to do based on pattern matching the types of objects in the queue.

    Parameters
    ----------
    queue
        Asyncio queue to consume tasks from, which should be Request types or functors
    pool
        Database pool to write results to
    http_client
        HTTP connection pool to speak to third parties with
    vae
        ML model for inference
    secrets_env
        Environment variables including API keys
    ignore_exceptions
        If True, just log about exceptions and crack on. If False, then bail out (probably horribly)

    Returns
    -------
    Never
        Kill the task to end this routine.
    """
    logger = getLogger(__name__)
    while True:
        # TODO (2025-08-29 MHJB): log job started in queue here
        job = await queue.get()
        future: Any = None  # eat the return types of the jobs we submit
        try:
            match job:
                case GridCO2Request():
                    future = await generate_grid_co2(job, pool=pool, http_client=http_client)
                case HeatingLoadRequest():
                    future = await generate_heating_load(params=job, pool=pool, http_client=http_client)
                case ElectricalLoadRequest():
                    future = await generate_electricity_load(params=job, vae=vae, pool=pool, http_client=http_client)
                case RenewablesRequest():
                    future = await generate_renewables_generation(
                        params=job, pool=pool, http_client=http_client, secrets_env=secrets_env
                    )
                case RenewablesWindRequest():
                    future = await generate_wind_generation(
                        params=job, pool=pool, http_client=http_client, secrets_env=secrets_env
                    )
                case TariffRequest():
                    future = await generate_import_tariffs(params=job, pool=pool, http_client=http_client)
                case ASyncFunctionRequest():
                    future = await job.func(*job.args, **job.kwargs)
                case SyncFunctionRequest():
                    with ThreadPoolExecutor() as thread_pool:
                        loop = asyncio.get_running_loop()
                        await loop.run_in_executor(thread_pool, job.func, *job.args, **job.kwargs)
                case _:
                    raise ValueError(f"Unhandled {type(job)}")
            logger.info(future)
        except Exception:
            # TODO (2025-08-29 MHJB): log failure in database here
            if ignore_exceptions:
                logger.exception("Internal exception in task queue")
            else:
                queue.task_done()
                raise
        # TODO (2025-08-29 MHJB): log completion in database here
        # also check if none are remaining in queue 
        queue.task_done()


_QUEUE: PrepochJobQueueT = Queue[GenericJobRequest]()


async def get_job_queue() -> PrepochJobQueueT:
    """
    Get the queue with tasks in it.

    Returns
    -------
    PrepochJobQueueT
        An initialised, but maybe empty, job queue.
    """
    return _QUEUE


JobQueueDep = typing.Annotated[PrepochJobQueueT, Depends(get_job_queue)]
