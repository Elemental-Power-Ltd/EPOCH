import asyncio
import datetime
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .dependencies import get_http_client
from .internal.log import logger
from .routers import epl_queue, metrics, optimise, simulate
from .routers.epl_queue import IQueue
from .routers.optimise import process_requests


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Create queue that is served by process_requests from moment app is created until it is closed."""
    q = IQueue(maxsize=20)
    app.state.q = q
    app.state.start_time = datetime.datetime.now(datetime.UTC)
    http_client = await get_http_client().__anext__()
    # https://textual.textualize.io/blog/2023/02/11/the-heisenbug-lurking-in-your-async-code/
    app.state._queue_task = asyncio.create_task(process_requests(q=q, http_client=http_client))
    yield
    app.state._queue_task.cancel()


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
