"""Lifespan tasks including job queues and databases."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, Never

from fastapi import Depends, FastAPI

from .dependencies import db, get_db_pool, get_http_client, get_secrets_dependency, get_thread_pool, get_vae_model
from .job_queue import TerminateTaskGroup, TrackingQueue, process_jobs

NUM_WORKERS = 2

_QUEUE: TrackingQueue | None = None


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
        _QUEUE = TrackingQueue(pool=await get_db_pool().__anext__())
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

    queue = await get_job_queue()
    async with asyncio.TaskGroup() as tg:
        for _ in range(NUM_WORKERS):
            _ = tg.create_task(
                process_jobs(
                    queue,
                    pool=db.pool,
                    http_client=await get_http_client().__anext__(),
                    vae=await get_vae_model(),
                    secrets_env=await get_secrets_dependency(),
                    ignore_exceptions=True,
                )
            )
        yield  # type: ignore
        # Shutdown events
        queue.shutdown()
        await queue.join()
        raise TerminateTaskGroup()
