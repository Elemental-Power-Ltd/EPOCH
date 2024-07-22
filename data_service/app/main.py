import os
from contextlib import asynccontextmanager
from typing import Any, Awaitable, Callable

import asyncpg
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .routers import client_data, meter_data, weather


class Database:
    async def create_pool(self):
        self.pool = await asyncpg.create_pool(
            dsn=os.environ.get("DATABASE_URL", "postgresql://python:elemental@localhost/elementaldb")
        )


db = Database()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Set up a long running database pool ready for requests.
    """
    # Load the ML model
    await db.create_pool()
    yield
    # cleanup here


app = FastAPI(lifespan=lifespan)
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def db_session_middleware(request: Request, call_next: Callable[[Request], Awaitable[Any]]):
    """
    Set up the database connection pool as part of the request object.
    """
    request.state.pgpool = db.pool
    response = await call_next(request)
    return response


app.include_router(client_data.router)
app.include_router(meter_data.router)
app.include_router(weather.router)


@app.get("/")
async def root():
    return {"message": "Welcome to the Data Elemental backend API!"}
