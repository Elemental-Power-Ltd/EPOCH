# Optimisation Elemental
***Matt Bailey, Will Drouard and Jon Warren***

This is a set of API endpoints that provide data services for Elemental Power.
Data services is a broad topic, but it includes client metadata (which sites belong to which clients, where sites are),
client utilities data (electricity, gas, occupancy, other sensors) and simulation input data (both real and synthetic).

It is implemented using FastAPI, wrapping around a PostgreSQL database. All database interaction should happen via
the FastAPI wrapping endpoints.

## Getting Started

To get started with this repository, run
```
    git clone git@github.com:Elemental-Power-Ltd/data_elemental.git
```
It is then easiest to run these services in a Docker compose set of containers, which will keep the database and API running together.
To do so, run
```
    docker compose up --build
```
in your terminal or command prompt. 
Using the Docker Desktop GUI isn't currently supported (mostly as I haven't written instructions for it yet).
The docker compose script will currently look for two initial SQL files to populate the databases. 
These are called `elementaldb_tables.sql` for the table structure and schemas, and `elementaldb_client_info.sql` for a set of dummy client info.
These should be placed in the same directory as your `docker-compose.yml` file, but you can start the service without them.
If you start the service without them, make sure that you add some client data manually or the foreign key constraints will fail.

By default, the data service will run on port `8762` and the database on port `5432`.

## Using These Endpoints

The endpoints provided here all take unauthenticated `POST` requests with a JSON body containing the parameters.
For example, one such request might be
```
    curl --request POST --header "Content-Type: application/json" http://localhost:8762/list-clients 
```
which would return a list of clients.

Or, to pass an argument, you might send

```
    curl --request POST --header "Content-Type: application/json" --data '{"client_id": "demo"}' http://localhost:8762/list-sites
```
which would return a list of sites associated with the `"demo"` client.

Endpoints are often split into `generate-*` and `get-*` types, for example `generate-heating-load` and `get-heating-load`.

### Generate Endpoints
In order to use a set of data, you must first call the `generate-*` endpoint with some parameters describing the data you
want to generate. This is often a `site_id`, and some originating set of data (for example, a gas meter dataset ID, or a
given external tariff). This will generally create some data for you and file it in the PostgreSQL database, and return too
you a unique dataset ID. Keep this to hand for the next stage!

### Get Endpoints
Then, you must call the `get-*` endpoint with that dataset ID, and often a pair of `start_ts`, `end_ts` timestamps.
For example, you might call
```
curl --request POST --header "Content-Type: application/json" --data '{"dataset_id": "b2375ee0-29e5-4e39-8ff1-bd2d41e74696", "start_ts": "2024-01-01T00:00:00Z", "end_ts": "2025-01-01T00:00:00Z"}' http://localhost:8762/get-heating-load
```
to get the gas meter readings associated with dataset `b2375ee0-29e5-4e39-8ff1-bd2d41e74696`.
Be careful about the timestamps, as these will sometimes resample the data to the period you have requested (if it is synthetic
data, or easily resample-able) or truncate it (if it cannot be resampled, e.g. tariffs which are only valid between certain
dates).

### List Endpoints

If you wish to see what data are available, try the `list-*` endpoints, e.g. `list-sites` as used above. These work in
the same format, and will return a list of the relevant data type. 
It is your responsibility to make sure that you keep track of which dataset IDs correspond to which types of dataset.
For example, if you try to request a heating load with a dataset ID that corresponds to solar PV generation, you are
likely to get an empty response (in future there may be error handling for this case).

## Input and Output Validation

The endpoints here make heavy use of pydantic. This will validate the messages you send in, and reject ill-formed messages.
Make sure that your messages correspond to the schemas specified in the docs.
You may look at the pydantic schemas in the `./models/` directory, which follows an almost parallel structure to the
`./routers/` directory.

All datetimes passed in must have a timezone attached. It is probably best if you hand everything over in UTC time, e.g. in the form `2024-01-01T00:00:00Z` as an ISO8601 string.
All UUIDs passed in are currently UUIDv4.
This may change in future.

If your message fails validation, you will receive a `422 Unprocessable Entity` response, with details about what failed.


## Database Structure

See `README_DATABASE.md` for information on how the database is structured.

## Contributing

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
If you are using these, there is a shared connection pool available in a `request: Request` object that you can pass to your endpoints.
To get a database connection from the pool, use the `request.state.pgpool` attribute as follows:
```
async with request.state.pgpool.acquire() as conn:
        foo = await conn.execute(...)
```
An `httpx.AsyncClient` is available similarly as `request.state.http_client`.
Please make sure you don't accidentally close these in your functions.
