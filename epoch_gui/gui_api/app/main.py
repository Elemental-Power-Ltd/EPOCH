from fastapi import FastAPI, Request, HTTPException
from fastapi.encoders import jsonable_encoder

from fastapi.middleware.cors import CORSMiddleware
import httpx
import uuid

from gui_api.app.models.types import ListSitesRequest

app = FastAPI(title="GUI_API")
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/get-status/")
async def get_status(request: Request):
    with httpx.Client() as client:
        response = client.post(url="http://127.0.0.1:8001/queue-status")
        return response.json()


@app.post("/submit-optimisation-job/")
async def submit_optimisation_job(request: Request):
    json_data = await request.json()
    with httpx.Client() as client:
        response = client.post(url="http://127.0.0.1:8001/submit-task", json=json_data)
        return response.json()


@app.post("/list-sites/")
async def list_sites(request: ListSitesRequest):
    with httpx.Client() as client:
        response = client.post(url="http://127.0.0.1:8002/list-sites", json=jsonable_encoder(request))
        return response.json()


@app.post("/list-optimisation-tasks/")
async def list_optimisation_tasks(request: Request):
    json_data = await request.json()
    with httpx.Client() as client:
        response = client.post(url="http://127.0.0.1:8002/list-optimisation-tasks", json=json_data)
        return response.json()


@app.post("/get-optimisation-results/")
async def get_optimisation_results(request: Request):
    json_data = await request.json()
    with httpx.Client() as client:
        response = client.post(url="http://127.0.0.1:8002/get-optimisation-results", json=json_data)
        return response.json()
