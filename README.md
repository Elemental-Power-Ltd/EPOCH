# Elemental Deployment

![inti](./inti.png)

Inti inits Elemental Power services.

## Initial Set Up

1. ⚠️ This repository contains submodules. 
   Clone it with: `git clone --recurse-submodules git@github.com:Elemental-Power-Ltd/inti.git`
2. Generate a Github Personal Access Token (classic)
3. Log in to the github container registry with `docker login ghcr.io -u $Username` (supplying your access token generated above)
4. Provide the secrets needed - see below for [more information](#secrets)
5. (Windows only) - Enable `network_mode: host`
   This can currently be found in `Settings > Resources > Network` in Docker Desktop


___

## How do I: 
___


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


## Convenience Scripts

The docker commands above have been written out in full, but you can use the scripts `dev-up` and `drop-db` within the scripts folder instead.
There are `.bat` and `.sh` versions of these scripts.

## Gotchas

### `$FOO is a directory`
   
When no file is present for a volume mapping, docker will assume this is a mapping for a directory and so create an empty directory. If you're seeing this error, it's likely either for:
- copy-migrations.sh - you haven't cloned the submodules for this repo!
- One of the secrets files

In both instances, you will need to remove that volume before it can be successfully remapped as a file. 


## Troubleshooting

The following docker commands are useful starting points

- `docker ps` list all running containers. Use `docker ps -a` to include stopped containers
- `docker images` list all images downloaded on to your machine.
- `docker logs $container_id` see the logs for a given service

## Secrets

The `secrets` section of docker-compose.yml defines file paths to read secrets from. 

They can be provided by creating these files (in the same directory as docker-compose.yml)

| Secrets File                         | Value                                                                           |
|--------------------------------------|---------------------------------------------------------------------------------|
| EP_POSTGRES_PASSWORD_FILE.txt        | An empty file - by default the docker postgres instance does not set a password |
| EP_VISUAL_CROSSING_API_KEY_FILE.txt  | Speak to Matt Bailey to obtain a copy                                           |
| EP_RENEWABLES_NINJA_API_KEY_FILE.txt | Create an account and generate a free API key for yourself                      |