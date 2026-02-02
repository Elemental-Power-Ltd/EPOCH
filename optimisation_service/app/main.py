import asyncio
import datetime
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.internal.epoch.version import get_epoch_version
from app.internal.log import configure_logging
from app.internal.task_processor import process_tasks

from .dependencies import get_http_client, get_queue
from .routers import data, epl_queue, merge, metrics, optimise, simulate

configure_logging()
logger = logging.getLogger("default")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Create queue that is served by process_requests from moment app is created until it is closed."""
    app.state.start_time = datetime.datetime.now(datetime.UTC)
    logger.info(f"Using EPOCH version: {get_epoch_version()}")
    queue = get_queue()
    http_client = await get_http_client()
    try:
        async with asyncio.TaskGroup() as tg:
            task = tg.create_task(process_tasks(queue=queue, http_client=http_client))
            yield
            # Shutdown events
            with suppress(TimeoutError):
                await asyncio.wait_for(queue.join(), timeout=10.0)
            task.cancel()
    except* Exception as eg:
        for e in eg.exceptions:
            logger.exception("Got exception:", repr(e))
        raise


app = FastAPI(lifespan=lifespan, title="Optimisation", root_path="/api/optimisation")

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Exception handler that logs a validation issue."""
    logger.error(f"Validation error: {exc.errors()} | Body: {exc.body}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )


@app.get("/")
async def read_main() -> dict[str, str]:
    """Welcome function to check the API is working."""
    return {"message": "Welcome to the Optimisation API!"}


app.include_router(optimise.router)
app.include_router(epl_queue.router)
app.include_router(simulate.router)
app.include_router(metrics.router)
app.include_router(merge.router)
app.include_router(data.router)
