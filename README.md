# EPOCH: Elemental Power Optimiser with Clean Heat

EPOCH is a set of tools to simulate local site energy systems, and to find optimal combinations of components.

## Usage

EPOCH comes in two forms: a full optimisation system and an individual calculator.

The full optimisation system allows you to upload data from your utility meters and combines it with tariff, weather and solar generation data to get a clear half hourly picture of your site's energy demands.
<img width="1424" height="1243" alt="image" src="https://github.com/user-attachments/assets/013922d5-3202-4b07-81bc-153de6d365c9" />

You can then specify a range of components such as heat pumps, solar panels and batteries that you're interested in
<img width="1354" height="1190" alt="image" src="https://github.com/user-attachments/assets/3daead84-430b-4471-8f00-c636cff91c31" />

These are passed through a smart optimiser which will find the best combination of assets to meet your cost and carbon needs on that site, providing detailed recommendations and analysis of how much they'll save.
<img width="1085" height="722" alt="image" src="https://github.com/user-attachments/assets/2aa451d8-7839-498d-a8fc-21827a4c0fa9" />


## Components

EPOCH is split into a number of components centered around a main simulator.
You can either run the "Epoch Server" for a quickstart to run individual simulators, or the whole set for optimisation and web hosting.

### Epoch Simulator
Epoch Simulator is the core energy simulation tool: it is a C++ programme (or library) that takes in time series energy consumption data, 
specified local site energy components, and outputs new costs and carbon emissions.

### Epoch Server
Epoch Server is a quickstart tool to run individual simulations in simplified cases.
This requires a built version of the Epoch Simulator python library and provides a simple FastAPI interface.
You can run it with `fastapi run` in the `epoch_server` directory.

We have pre-baked some example data for three sites representing reasonable energy consumption, solar generation and heat demands across a sample year.

### Data Service

The Data Service collects data from third parties and stores it in a PostgreSQL database.
It also runs machine learning and statistical inference and upsampling, taking in low quality meter readings and turning them into consistent halfhourly data.

### Optimisation Service

The Optimisation Service acts between the GUI and the database, working on optimisation jobs to find the best combination of parameters.
This requires a built version of the Epoch Simulator python library.

### Epoch GUI

The GUI is different to Epoch Server: this is the fully-featured GUI with optimisation and data upload capabilities.
This requires the data and optimisation components to be running.


## Getting Started

### Run the latest build of each service with docker postgres?

`docker compose -f docker-compose.yml -f docker-compose.dev.yml up`

### Run the latest build of each service with native postgres?

`docker compose up`
___

### Run one (or more) of the services locally with the others running in docker?

1. Comment out the services you want to run locally, in both `docker-compose.yml` and `docker-compose.dev.yml`

2. Run: `docker-compose -f docker-compose.yml -f docker-compose.dev.yml up`


### Test a locally built docker image out?

1. Build your target service by running `docker-compose build` within that service's docker directory (noting the image name and tag)
2. Change that service's image tag in `docker-compose.yml` from `ghcr.io/elemental-power-ltd/{service}:{tag}` to `{service}:{tag}`

### Delete and re-initialise the docker postgres database?

1. Drop the volume:

    `docker-compose -f docker-compose.yml -f docker-compose.dev.yml down -v`

2. Restart the services

    `docker-compose -f docker-compose.yml -f docker-compose.dev.yml up`

### Convenience Scripts

The docker commands above have been written out in full, but you can use the scripts `dev-up` and `drop-db` within the scripts folder instead.
There are `.bat` and `.sh` versions of these scripts.


## Gotchas & Troubleshooting

### Troubleshooting

The following docker commands are useful starting points

- `docker ps` list all running containers. Use `docker ps -a` to include stopped containers
- `docker images` list all images downloaded on to your machine.
- `docker logs $container_id` see the logs for a given service

### `$FOO is a directory`
   
When no file is present for a volume mapping, docker will assume this is a mapping for a directory and so create an empty directory. If you're seeing this error, it's likely either for:
- copy-migrations.sh - you haven't cloned the submodules for this repo!
- One of the secrets files

In both instances, you will need to remove that volume before it can be successfully remapped as a file. 
