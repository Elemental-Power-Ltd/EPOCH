# Deploying the Service Architecture

## Summary

Use `docker compose up` to run all of the services

Use `docker compose -f docker-compose.yml -f docker-compose.dev.yml up` to override settings for local development, including providing a postgres container.

## Overview

Each of our services can be built by a manually triggered **Create and Publish** github action. These actions will upload a docker image to the github container registry, tagged with the branch name.

Running `docker compose up` will pull these images if necessary. You will need to generate a GitHub access token and run `docker login` to do this for the first time.

## Environment Variables

`EP_OPTIMISATION_SERVICE_URL`: The hostname and port for the optimisation service

`EP_DATA_SERVICE_URL`: The hostname and port for the data service

`EP_DATABASE_HOST`: The IP address for the database

## Secrets

Secrets for API keys and database access can be read from a number of different places.

The following secrets may be required:

`EP_POSTGRES_PASSWORD` - set as appropriate for your postgres instance. Leave blank for a docker container instance.

`EP_VISUAL_CROSSING_API_KEY`

`EP_RENEWABLES_NINJA_API_KEY`

