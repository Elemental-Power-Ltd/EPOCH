"""Tests for Air Source heat Pump related endpoints."""

# ruff: noqa: D101, D102
import itertools

import numpy as np
import pytest
import pytest_asyncio
from httpx import AsyncClient
from pydantic import Json

from app.internal.utils.uuid import uuid7


@pytest.fixture
def demo_ashp_uuid() -> str:
    """Get an (ignored) UUID for an ASHP dataset."""
    return str(uuid7())


@pytest_asyncio.fixture
async def ashp_input_response(client: AsyncClient, demo_ashp_uuid: str) -> Json:
    """Get an example set of ASHP input data."""
    return (await client.post("/get-ashp-input", json={"dataset_id": demo_ashp_uuid})).json()


@pytest_asyncio.fixture
async def ashp_output_response(client: AsyncClient, demo_ashp_uuid: str) -> Json:
    """Get an example set of ASHP input data."""
    return (await client.post("/get-ashp-output", json={"dataset_id": demo_ashp_uuid})).json()


@pytest.mark.asyncio
class TestASHPInputs:
    @pytest.mark.asyncio
    async def test_temperatures_count_up(self, ashp_input_response: Json) -> None:
        data = np.array(ashp_input_response["data"])
        for first, second in itertools.pairwise(data[1:, 0]):
            assert second > first, "Index temperatures must count up"

        for first, second in itertools.pairwise(data[0, 1:]):
            assert second > first, "Column temperatures must count up"

    # @pytest.mark.asyncio
    # async def test_cop_reasonable(self, ashp_input_response: Json) -> None:
    #    assert all(
    #        all(item > 1 for item in sublist) for sublist in ashp_input_response["data"]
    #    ), "Coefficients of performance must be >1"


@pytest.mark.asyncio
class TestASHPOutputs:
    @pytest.mark.asyncio
    async def test_temperatures_count_up(self, ashp_output_response: Json) -> None:
        data = np.array(ashp_output_response["data"])
        for first, second in itertools.pairwise(data[1:, 0]):
            assert second > first, "Index temperatures must count up"

        for first, second in itertools.pairwise(data[0, 1:]):
            assert second > first, "Column temperatures must count up"

    # @pytest.mark.asyncio
    # async def test_cop_reasonable(self, ashp_output_response: Json) -> None:
    #    assert all(
    #        all(item > 1 for item in sublist) for sublist in ashp_output_response["data"]
    #    ), "Coefficients of performance must be >1"
