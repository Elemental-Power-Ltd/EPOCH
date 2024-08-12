"""
Common configuration for pytest.

This has to be at the bottom for plugin imports, but please prefer more localised `conftest.py` files
or ideally `pyproject.toml`.
"""

pytest_plugins = ("pytest_asyncio",)
