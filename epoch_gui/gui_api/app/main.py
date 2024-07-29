from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import uuid


app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/submit-optimisation-job/")
async def submit_optimisation_job(request: Request):
    try:
        payload = await request.json()
        print(f"Received optimiser: {payload['optimiser']}")

        # Generate a TaskID for the task
        payload["TaskID"] = str(uuid.uuid1())

        # FIXME - timewindow removed until it is added to the python bindings
        del payload["searchParameters"]["timewindow"]
        payload["optimiserConfig"] = {}

        # Add the objectives as hardcoded values (until they are added to the gui)
        payload["objectives"] = [
            "carbon_balance",
            "cost_balance",
            "capex",
            "payback_horizon",
            "annualised_cost"
        ]

        with httpx.Client() as client:
            response = client.post(url="http://127.0.0.1:8001/submit-task/", json=payload)

        # async with httpx.AsyncClient as client:
        #     response = await client.post(url="http://127.0.0.1:8001/submit-task/", json=payload)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code,
                                detail="Unable to submit task")

        return {"status": "success", "message": "Job submitted successfully to both services"}

    except Exception as e:
        print(f"Failed to submit task: {e}")
        raise HTTPException(status_code=500, detail=str(e))
