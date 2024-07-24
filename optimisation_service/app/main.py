import asyncio
import time
from concurrent.futures import ProcessPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .routers import optimise, queue
from .routers.optimise import process_requests
from .routers.queue import IQueue


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Create queue that is served by process_requests from moment app is created until it is closed.
    """
    q = IQueue(maxsize=5)
    pool = ProcessPoolExecutor()
    start_time = time.time()
    app.state.q = q
    app.state.pool = pool
    app.state.start_time = start_time
    asyncio.create_task(process_requests(q, pool))
    yield
    pool.shutdown()


app = FastAPI(lifespan=lifespan)

app.include_router(optimise.router)
app.include_router(queue.router)

# @app.get("/records")
# async def get_records():
#     return records
