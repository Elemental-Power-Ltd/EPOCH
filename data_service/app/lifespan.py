"""Lifespan tasks including job queues and databases."""

import asyncio
import contextvars
import datetime
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, Never

from fastapi import Depends, FastAPI

from .dependencies import db, get_db_pool, get_http_client, get_secrets_dep, get_thread_pool, get_vae_model
from .job_queue import TerminateTaskGroup, TrackingQueue, mark_remaining_jobs_as_error, process_jobs

NUM_WORKERS = 2
FINAL_JOIN_TIMEOUT = datetime.timedelta(seconds=10)
_QUEUE: TrackingQueue | None = None
WORKERS: list[asyncio.Task] = []


async def get_job_queue() -> TrackingQueue:
    """
    Get the queue with tasks in it.

    Returns
    -------
    PrepochJobQueueT
        An initialised, but maybe empty, job queue.
    """
    global _QUEUE
    if _QUEUE is None:
        _QUEUE = TrackingQueue(pool=await get_db_pool())
    return _QUEUE


JobQueueDep = Annotated[TrackingQueue, Depends(get_job_queue)]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[Never]:
    """Set up a long clients: a database pool and an HTTP client."""
    # Startup events
    loop = asyncio.get_running_loop()
    thread_pool = await get_thread_pool()
    loop.set_default_executor(thread_pool)
    await db.create_pool()
    assert db.pool is not None, "Failed to create DB pool"
    await mark_remaining_jobs_as_error(db.pool, "Hanging job tidied on startup")
    queue = await get_job_queue()
    try:
        async with asyncio.TaskGroup() as tg:
            for idx in range(NUM_WORKERS):
                ctx = contextvars.copy_context()
                WORKERS.append(
                    tg.create_task(
                        process_jobs(
                            queue,
                            pool=db.pool,
                            http_client=await get_http_client(),
                            vae=await get_vae_model(),
                            secrets_env=get_secrets_dep(),
                            ignore_exceptions=True,
                        ),
                        name=f"Worker {idx}",
                        context=ctx,
                    )
                )
            # This is the bit that actually "returns" the client
            yield  # type: ignore

            # We've received a SIGTERM so wait 10s for stragglers to finish, then kill the task
            # and tidy up.
            await asyncio.wait_for(queue.join(), FINAL_JOIN_TIMEOUT.total_seconds())
            raise TerminateTaskGroup()
    except* TerminateTaskGroup:
        pass
    except* TimeoutError:
        await mark_remaining_jobs_as_error(
            db.pool, f"Terminated on cleanup due to {FINAL_JOIN_TIMEOUT.total_seconds()}s timeout."
        )
    except* Exception as ex:
        ex_str = type(ex).__name__
        if ex.args:
            ex_str += ": " + ",".join(ex.args)
        await mark_remaining_jobs_as_error(db.pool, "Terminated on cleanup due to" + ex_str)
