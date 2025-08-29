"""Job queue for background tasks, including dataset generation."""

import asyncio
import json
from collections.abc import Awaitable, Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from enum import StrEnum, auto
from logging import getLogger
from typing import Any

from httpx import AsyncClient

from app.epl_secrets import SecretDict
from app.internal.elec_meters import VAE
from app.internal.epl_typing import db_pool_t
from app.models.carbon_intensity import GridCO2Request
from app.models.core import dataset_id_t
from app.models.electricity_load import ElectricalLoadRequest
from app.models.heating_load import HeatingLoadRequest
from app.models.import_tariffs import TariffRequest
from app.models.renewables import RenewablesRequest, RenewablesWindRequest
from app.routers.carbon_intensity import generate_grid_co2
from app.routers.electricity_load import generate_electricity_load
from app.routers.heating_load import generate_heating_load
from app.routers.import_tariffs import generate_import_tariffs
from app.routers.renewables import generate_renewables_generation, generate_wind_generation


class JobStatusEnum(StrEnum):
    """Mark the status of a job within the database."""

    Queued = auto()
    Working = auto()
    Error = auto()
    Completed = auto()


class TerminateTaskGroup(Exception):
    """Exception raised to terminate a task group.

    Use this to end the processing of a queue.
    """


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


class TrackingQueue(asyncio.Queue[tuple[int, GenericJobRequest]]):
    """
    A job tracking queue that also logs to the database.

    Each job is secretly given a database ID, and status updates are written.
    As a rough guide:
    * `.put(item)` will insert it in the database with status `queued`
    * `.get(item)` will update the database with status `working`
    * `.mark_done(None)` will update the database with status `completed`
    * `.mark_done(ex)` will update the database with status `error`

    Internally items are stored as a `(job_id, request)` pair but only the `request` object is exposed.
    """

    def __init__(self, pool: db_pool_t, maxsize: int = 0):
        """
        Set up the queue with access to a database.

        Parameters
        ----------
        pool
            Database pool to write updates into
        maxsize
            Maximum queue size, `.put(item)` will block if qsize > maxsize
        """
        self.pool = pool
        # This is how we track which job is currently being worked on
        # it's set in ".get" and cleared in ".mark_done"
        # TODO (2025-08-29 MHJB): what if there are two consumers?
        self._last_job_id: int | None = None
        super().__init__(maxsize=maxsize)

    def items(self) -> list[GenericJobRequest]:
        """
        Get all the current items in the queue.

        This has no guarantee of ordering, and items might have been taken from the queue
        at any time during this call.

        Returns
        -------
        list[GenericJobRequest]
            List of requests in the queue at the moment you called this.
        """
        assert hasattr(self, "_queue"), "Internal queue not initialised"
        assert self._queue is not None, "Internal queue not initialised"
        return [item[1] for item in self._queue]

    async def put(self, item: GenericJobRequest) -> None:  # type: ignore[override]
        """
        Put a new item in the queue.

        This will insert it into the database with status 'queued'.

        Parameters
        ----------
        item
            Item to insert into the queue
        """
        job_id = await self.pool.fetchval(
            """
            INSERT INTO job_queue.job_status (
                job_type,
                job_status,
                bundle_id,
                request)
            VALUES ($1, $2, $3, $4)
            RETURNING job_id""",
            type(item).__name__,
            JobStatusEnum.Queued,
            item.bundle_metadata.bundle_id if hasattr(item, "bundle_metadata") else None,  # type: ignore
            item.model_dump_json(),
        )
        return await super().put((int(job_id), item))

    async def get_with_id(self) -> tuple[int, GenericJobRequest]:
        """
        Get an item from the queue with its ID.

        This will mark it as `working` in the database.

        Returns
        -------
        tuple[int, GenericJobRequest]
            The ID of a database item, an item to work on
        """
        job_id, job = await super().get()
        await self.pool.execute(
            """
            UPDATE job_queue.job_status SET
                job_status = $1,
                started_at = NOW()
            WHERE job_id = $2""",
            JobStatusEnum.Working,
            job_id,
        )
        # mark this ID as the most recent one we've seen
        self._last_job_id = job_id
        return job_id, job

    async def get(self) -> GenericJobRequest:  # type: ignore[override]
        """
        Get an item from the queue.

        This will mark it as `working` in the database.

        Returns
        -------
        GenericJobRequest
            an item to work on
        """
        return (await self.get_with_id())[1]

    async def task_done(self, job_id: int | None = None, ex: Exception | None = None) -> None:  # type: ignore[override]
        """
        Mark an item as done.

        This will mark it as `completed` or `error` in the database dependin on `ex`

        Parameters
        ----------
        job_id
            The ID of the job to mark as done. If not provided, use the ID of the last checked out job.
        ex
            If None, mark this job as completed
            If an exception, mark this job as an error with detail set to info about this problem

        Returns
        -------
        None
        """
        if job_id is None:
            job_id = self._last_job_id
        if ex is None:
            await self.pool.execute(
                """
            UPDATE job_queue.job_status SET
                job_status = $1,
                completed_at = NOW()
            WHERE job_id = $2""",
                JobStatusEnum.Completed,
                job_id,
            )
        else:
            ex_str = str(ex)
            if ex.args:
                ex_str += ":" + ",".join(ex.args)
            await self.pool.execute(
                """
            UPDATE job_queue.job_status SET
                job_status = $1,
                completed_at = NOW(),
                detail = $2
            WHERE job_id = $3""",
                JobStatusEnum.Error,
                ex_str,
                job_id,
            )
        self._last_job_id = None
        super().task_done()


def is_bundle_in_queue(bundle_id: dataset_id_t, queue: TrackingQueue) -> bool:
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
    internal_queue: Iterable[GenericJobRequest] = queue.items()
    return any(
        hasattr(item, "bundle_metadata") and item.bundle_metadata.bundle_id == bundle_id  # type: ignore
        for item in internal_queue
    )


async def process_jobs(
    queue: TrackingQueue,
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
        job_id, job = await queue.get_with_id()
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
        except Exception as ex:
            await queue.task_done(job_id=job_id, ex=ex)
            if ignore_exceptions:
                logger.exception("Internal exception in task queue")
            else:
                raise
        else:
            # also check if none are remaining in queue?
            await queue.task_done(job_id=job_id)
