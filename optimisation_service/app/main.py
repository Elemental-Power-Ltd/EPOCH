import asyncio
import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

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
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
    q = IQueue(maxsize=5)
    start_time = time.time()
    app.state.q = q
    app.state.start_time = start_time
    asyncio.create_task(process_requests(q))
    yield


app = FastAPI(lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logging.error(f"Validation error: {exc.errors()} | Body: {exc.body}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )


app.include_router(optimise.router)
app.include_router(queue.router)
