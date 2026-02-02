# Optimisation Elemental
***Matt Bailey, Will Drouard and Jon Warren***

This is a set of API endpoints that provide optimisation services for Elemental Power.

It is implemented using FastAPI and leverages Epoch Simulator for simulations.

## Getting Started

Running the service requires the data services to be running first, and a built copy of Epoch Simulator.
It is then easiest to run these services in a container.
To do so, run
```
    docker compose -f docker/docker-compose.yml up
```
in your terminal.

By default, the optimisation service will run on port `8761`.

## Using the Endpoints

The endpoints provided here all take unauthenticated `POST` requests with a JSON body containing the parameters.
For example, one such request might be
```
    curl --request POST --header "Content-Type: application/json" http://localhost:8761/queue-status
```
which would return any current optimisation tasks and information about the service.

Or, to pass an argument, you might send

```
    curl --request POST --header "Content-Type: application/json" --data '{"task_id": "435b6e72-0e0e-40a9-97e4-461036c59230"}' http://localhost:8761/cancel-task
```
which would remove the optimisation task associated with `435b6e72-0e0e-40a9-97e4-461036c59230` from the queue.

### Submitting Optimisation Tasks

An optimisation task can be added to the service's queue by using the `submit-task` endpoint. Succesful submissions will return a JSON body containing a `task_id` which is unique to the task.
The POST request requires a JSON body containing the following:

#### Optimiser

A dictionary describing the optimiser to use. Must be in the format:
```
{
    "name": <Optimiser Name>,
    "hyperparameters": <Dictionary of Hyperparameters>
}
```

Their currently exists three optimiser options: `NSGA2`, `GeneticAlgorithm` and `GridSearch`.

#### Search Parameters

A dictionary of parameters and corresponding values for the optimiser in the format:
```
{
    "<Parameter Name>":
        "Min": <Mininum Paramter Value>,
        "Max": <Maxinum Paramter Value>,
        "Step": <Step size for the Parameter>
}
```

#### Objectives

A list of objectives to optimiser for:
The options include: `carbon_balance`, `cost_balance`, `capex`, `payback_horizon` and `annualised_cost`
See `metrics.py` for a complete list

#### Site Data

Dictionary describing the input data to use in the optimisation.
This can either be a path to local files in the following format:
```
{
    "loc": "local",
    "site_id": <ID associated with site>
    "path": <Path to local input files>
}
```
Or a description of data to fetch from the data service:
```
{
    "loc": "remote",
    "site_id": <ID associated with site>
    "start_ts": <Datetime to retrieve data from>
    "duration": <Length of time to retrieve data for>
}
```
The data must already have been generated for this to work.
Currently only `year` durations are functional.

### Retrieving Optimisation Results

Once an optimisation run is concluded, the results are directly transmited to the data service.
They can be retrieved from the data service by using the task's unique `task_id`.

### Cancelling Optimisation Tasks

Optimisation Tasks that are still in the services queue can be cancelled.
This can either be done by cancelling individual tasks the `cancel-task` endpoint as shown above or by cancelling all tasks in queue with the `clear-queue` endpoint.
