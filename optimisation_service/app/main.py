import asyncio
import datetime
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .routers import optimise, queue
from .routers.optimise import process_requests
from .routers.queue import IQueue

logger = logging.getLogger("default")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Create queue that is served by process_requests from moment app is created until it is closed.
    """
    q = IQueue(maxsize=5)
    app.state.q = q
    app.state.start_time = datetime.datetime.now(datetime.UTC)
    asyncio.create_task(process_requests(q))
    yield


app = FastAPI(lifespan=lifespan, title="Optimisation")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logging.error(f"Validation error: {exc.errors()} | Body: {exc.body}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )


@app.get("/")
async def read_main():
    return {"message": "Welcome to the Optimisation API!"}


app.include_router(optimise.router)
app.include_router(queue.router)
