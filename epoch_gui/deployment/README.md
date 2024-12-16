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

`EP_VISUAL_CROSSING_API_KEY` - **keep secret**, we only have a single key as an organization

`EP_RENEWABLES_NINJA_API_KEY` - per user and free, [create an account](https://renewables.ninja) to generate a key for yourself


## Database Configuration

When using `docker-compose.dev.yml` to run postgres through docker, there are a number of files and environment variables that must be mapped to perform first time setup. These are defined in the `db` service section.

### SQL Files

The db volume section maps three files: 
 - elementaldb_client_info.sql
 - elementaldb_tables.sql
 - elementaldb_client_meters.sql

Copies of `elementaldb_client_info.sql` and `elementaldb_tables.sql` can be obtained from the data_elemental repository.

`elementaldb_client_meters.sql` is larger and so we don't check this file into version control. Ask Matt Bailey for a copy.

### Environment settings

The db environment section defines default user/password settings. These can generally be left as is.