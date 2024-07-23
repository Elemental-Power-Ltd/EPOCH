import asyncio
from concurrent.futures import ProcessPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .routers import optimise
from .routers.optimise import process_requests


@asynccontextmanager
async def lifespan(app: FastAPI):
    queue = asyncio.Queue(maxsize=5)
    pool = ProcessPoolExecutor()
    app.state.queue = queue
    app.state.pool = pool
    asyncio.create_task(process_requests(queue, pool))
    yield
    pool.shutdown()


app = FastAPI(lifespan=lifespan)

app.include_router(optimise.router)

# @app.get("/records")
# async def get_records():
#     return records
