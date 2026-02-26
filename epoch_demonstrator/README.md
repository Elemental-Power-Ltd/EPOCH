# Epoch Demonstrator

A minimal quickstart demonstrator to run single simulations with Epoch Simulator.

The Demonstrator is a FastAPI server that serves a minimal HTML form directly on `/`

## Quick Start

Run `docker compose build --up` and access the GUI from `localhost:8763`

## Available Data

We have pre-baked data for three sites: one in London, one in Cardiff, and one in Edinburgh.
Each site has three different size scales reflecting different building types, and four possible solar aspects oriented in the cardinal directions.

## Developing

To run locally, you will first need to:
- Build the epoch_simulator python bindings
- Install the demonstrator's other dependencies

The Dockerfile should serve as a blueprint for doing this.

## Integrating with the EPOCH Gui

For a more feature-rich version of the demonstrator, EPOCH Gui provides an alternative frontend. This includes energy usage bar charts of the resulting simulations.

![img.png](demonstrator_gui.png)

See the GUI's `package.json` for scripts to run and build this gui.

### Hosting

The EPOCH Gui Demonstrator sends requests to `/api/simulate`.
Use a reverse proxy (e.g. NGINX or Caddy) or change this directly to point at your instance of the backend. 

