# EPOCH: Elemental Power Optimiser with Clean Heat

EPOCH is a set of tools to simulate local site energy systems, and to find optimal combinations of components.


## Quick Start

If running for the first time, instead follow [first-time setup](#first-time-setup)

1. Run `docker compose up` from the root directory
2. Access the Epoch GUI on `http://localhost:8760`


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
You can either run the "Epoch Demonstrator" for a quickstart to run individual simulators, or the whole set for optimisation and web hosting.

### Epoch Simulator
Epoch Simulator is the core energy simulation tool: it is a C++ programme (or library) that takes in time series energy consumption data, 
specified local site energy components, and outputs new costs and carbon emissions.

### Data Service

The Data Service collects data from third parties and stores it in a PostgreSQL database.
It also runs machine learning and statistical inference and upsampling, taking in low quality meter readings and turning them into consistent halfhourly data.

### Optimisation Service

The Optimisation Service acts between the GUI and the database, working on optimisation jobs to find the best combination of parameters.
This requires a built version of the Epoch Simulator python library.

### Epoch GUI

The GUI is different to Epoch Demonstrator: this is the fully-featured GUI with optimisation and data upload capabilities.
This requires the data and optimisation components to be running.

### Epoch Demonstrator
Epoch Demonstrator is a standalone tool to run individual simulations in simplified cases.
This requires a built version of the Epoch Simulator python library and provides a simple FastAPI interface.
You can run it with `fastapi run` in the `epoch_demonstrator` directory.

We have pre-baked some example data for three sites representing reasonable energy consumption, solar generation and heat demands across a sample year.

## First-time setup
1. Install Docker
2. Provide the following [secrets](https://github.com/Elemental-Power-Ltd/EPOCH/development):
    - Create a RenewablesNinja account and place the API Key in a file called `./EP_RENEWABLES_NINJA_API_KEY_FILE.txt`
    - Create a filed called `./EP_POSTGRES_PASSWORD_FILE.txt` with the password `elemental`
    - [OPTIONAL] Create an OpenMeteo or VisualCrossing account and place the API Key in `./OPEN_METEO_API_KEY_FILE.txt` or `./VISUAL_CROSSING_API_KEY_FILE.txt` respectively. The free tier of OpenMeteo will be used if neither are specified
3. Build the services with `docker compose build` and then run with `docker compose up`
    - Or alternatively combine into `docker compose up --build`
4. Access the Epoch GUI on `localhost:8760`


## Development, troubleshooting and more

See the [development](https://github.com/Elemental-Power-Ltd/EPOCH/development) section of the Wiki
