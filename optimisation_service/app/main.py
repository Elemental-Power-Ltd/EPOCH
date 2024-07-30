import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI

from .routers import optimise, queue
from .routers.optimise import process_requests
from .routers.queue import IQueue


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Create queue that is served by process_requests from moment app is created until it is closed.
    """
    os.makedirs("./app/error_logs", exist_ok=True)
    logging.basicConfig(
        filename=f"./app/error_logs/error_log_{datetime.now(UTC).strftime('%Y_%m_%d_%H_%M_%S')}.log",
        level=logging.ERROR,
        format="%(asctime)s:%(levelname)s:%(message)s",
    )
    q = IQueue(maxsize=5)
    start_time = time.time()
    app.state.q = q
    app.state.start_time = start_time
    asyncio.create_task(process_requests(q))
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(optimise.router)
app.include_router(queue.router)
