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
    try:
        with httpx.Client() as client:
            response = client.post(url="http://127.0.0.1:8001/queue-status")

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Unable to get status")

        return response.json()

    except Exception as e:
        print(f"Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/submit-optimisation-job/")
async def submit_optimisation_job(request: Request):
    try:
        payload = await request.json()
        print(f"Received optimiser: {payload['optimiser']}")

        # Generate a TaskID for the task
        payload["task_id"] = str(uuid.uuid4())

        # Add the objectives as hardcoded values (until they are added to the gui)
        payload["objectives"] = [
            "carbon_balance",
            "cost_balance",
            "capex",
            "payback_horizon",
            "annualised_cost"
        ]

        # hardcode SiteData for now
        payload["site_data"] = {
            "loc": "local",
            "path": "../repro_inputs/GoodData"
        }

        # changes for latest version
        del payload["search_parameters"]["timewindow"]
        payload["task_name"] = "Name Hardcoded in GUI API"

        payload["optimiser"] = {"name": "GeneticAlgorithm", "hyperparameters": {}}
        payload["site_id"] = "demo_edinburgh"

        with httpx.Client() as client:
            response = client.post(url="http://127.0.0.1:8001/submit-task", json=payload)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code,
                                detail="Unable to submit task")

        return {"status": "success", "message": "Job submitted successfully to both services"}

    except Exception as e:
        print(f"Failed to submit task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
