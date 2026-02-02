from typing import cast

import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.models.metrics import MetricDirection


class TestMain:
    @pytest_asyncio.fixture
    async def metric_direction_response(self, client: AsyncClient) -> dict[str, int]:
        """Check that the JSON response from the metric endpoint is good and send it on as the right type."""
        resp = await client.get("/get-metric-directions")
        assert resp.status_code == 200, resp.text
        return cast(dict[str, int], resp.json())

    @pytest.mark.asyncio
    async def test_all_plus_minus_one(self, metric_direction_response: dict[str, int]) -> None:
        """Test that all the returned values are +/- 1"""
        assert all(item in {-1, 1} for item in metric_direction_response.values())

    @pytest.mark.asyncio
    async def test_matches_internal(self, metric_direction_response: dict[str, int]) -> None:
        """Test that all the responses match what we use internally."""
        for key, value in metric_direction_response.items():
            assert value == MetricDirection[key]
