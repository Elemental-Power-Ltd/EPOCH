"""Lifespan tasks including job queues and databases."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Never

from fastapi import FastAPI

from .dependencies import db, get_http_client, get_secrets_dependency, get_thread_pool, get_vae_model
from .job_queue import TerminateTaskGroup, get_job_queue, process_jobs


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
