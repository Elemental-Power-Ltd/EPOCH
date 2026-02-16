# Contributing

EPOCH is an open source-tool and we'd love your contributions.

## Issues

If you have an issue with this project, please use the GitHub issue tracker at https://github.com/Elemental-Power-Ltd/EPOCH/issues.
Provide as much context as you can, including whether you're using Docker, the platform you're running on (Mac, Windows, Linux etc). 
If you are having issues with the data generation process, try to include a minimal working example that demonstrates your problem.

## Pull Requests

To hve your contribution accepted, please open a pull request at https://github.com/Elemental-Power-Ltd/EPOCH/pulls.
We'll run code quality checkers, linters and CI pipelines to ensure that it doesn't break anything, and a maintainer will provide feedback (and hopefully merge your changes).

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
Some tests require external connections.
These are flaky and hard to replicate in CI, so mark them with `@pytest.mark.external`.
We will try to cache with a mocked HTTP client that intercepts the first call; the resultant files are saved as JSON in `data_service/tests/data`


### Pull Requests
Please contribute to this repository using a pull request system, and do not commit directly to `main`.
Make a branch with your work off `main` with one of the following tags:

* `feature/$BRANCH_NAME` for contributions of new features
* `bugfix/$BRANCH_NAME` for bugfixes (ideally linked to a github issue if one exists)
* `refactor/$BRANCH_NAME` for refactoring projects
* `chore/$BRANCH_NAME` for minor updating tasks (like a README)

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
To get a database connection from the pool, use the `DatabasePoolDep` attribute as follows:
```
    foo = await pool.execute(...)
```
## Contributing: C++

The C++ code lives in `core_simulator` and relies on C++20.

### Coding Style

### Packages

We use `vcpkg` to manage dependencies; please keep external dependencies to a minimum.