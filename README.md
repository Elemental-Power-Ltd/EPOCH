# EPOCH: Elemental Power Optimiser with Clean Heat
Inti inits Elemental Power services.

## Initial Set Up


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

## Contributing: Python

### Coding Style
The coding style for this repository is enforced by `mypy` and `ruff`.
All of your functions should be type-hinted, with all parameters and return objects specified until `mypy` is happy.
Ruff has a long list of rules set in `pyproject.toml`, and you should use it as both a formatter and a linter.
Before committing your code, please run
```
    ruff format . --preview && ruff check . --preview
```
and fix any results that it complains about (you can use ruff to autofix results with `ruff check . --preview --fix`).

### Tests
Please write as many tests as you think is reasonable using `pytest`, and place them in the `./tests` directory.
Group your tests into classes, and use fixtures for generating consistent requirements or datasets.

Try to keep your tests relatively fast, and use a test database (called `testdb` in PostgreSQL) for your tests.
This test database will be wiped and re-established with some test data, so don't rely on things persisting between runs. 
Please make sure you don't introduce any coupling between tests through this test database.

If your test is unavoidably slow, mark it with the pytest decorator `@pytest.mark.slow`.
These will be skipped by default, but can be run if you execute
```
    pytest -v -m "not slow"
```


### Pull Requests
Please contribute to this repository using a pull request system, and do not commit directly to `main`.
Make a branch with your work off `main` with one of the following tags:

* `feature/$BRANCH_NAME` for contributions of new features
* `bugfix/$BRANCH_NAME` for bugfixes (ideally linked to a github issue if one exists)
* `refactor/$BRANCH_NAME` for refactoring projects

Other tags are fine if you find that these don't work for you.
If `main` has changed since you branched off it, it is best to rebase onto main to get up to date and keep the git tree clean.
Merge commits are acceptable if they will keep the history cleaner and avoid git mangling.

### Continuous Integration

Every push to github will run a set of type checks, linting, and running unit tests.
Your pull request will not be merged until all of these are green, even minor failures.
Please run all of the relevant checks offline before submitting.

### Docstrings

Every function should have a docstring, and the CI will enforce this.
Your docstring should be in the numpy style, documented here: https://numpydoc.readthedocs.io/en/latest/format.html

An example docstring might look like:
```
def frobnicate(spam: int, eggs: str | None = None) -> BreakfastResponse:
    """
    Frobnicate some spam and eggs, with the first sentence in imperative style.

    Some more detail about how and why one would want to frobnicate spam and eggs,
    and what edge cases callers might expect (this will show up in FastAPI docs sometimes).

    Parameters
    ----------
    *spam*
        Compressed meat in a can, documenting a parameter
    *eggs*
        Hard calciferous parameter two, if None will construct a hens egg later on.

    Returns
    -------
    *breakfast_response*
        Spam and eggs combined, documenting what you should expect as a return

    Raises
    ------
    *AttributeError*
        Non-obvious exceptions that might be raised here
    """
    ...
```

### Async Style
As we're using FastAPI, you should expect your endpoints and any IO bound functions to be asynchronous.
Where possible, use `asyncpg` as the database driver and `httpx` as the HTTP request library.
If you are using these, there is a shared connection pool available via the FastAPI dependency injection framework.
To get a database connection from the pool, use the `DatabaseConnDep` or `DatabasePoolDep` attribute as follows:
```
async with pool.acquire() as conn:
        foo = await conn.execute(...)
```
An `httpx.AsyncClient` is available similarly as `request.state.http_client`.
Please make sure you don't accidentally close these in your functions.
