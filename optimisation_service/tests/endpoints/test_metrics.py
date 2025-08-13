from typing import cast

import pytest
from fastapi.testclient import TestClient

from app.models.metrics import MetricDirection


class TestMain:
    @pytest.fixture
    def metric_direction_response(self, client: TestClient) -> dict[str, int]:
        """Check that the JSON response from the metric endpoint is good and send it on as the right type."""
        resp = client.get("/get-metric-directions")
        assert resp.status_code == 200, resp.text
        return cast(dict[str, int], resp.json())

    def test_all_plus_minus_one(self, metric_direction_response: dict[str, int]) -> None:
        """Test that all the returned values are +/- 1"""
        assert all(item in {-1, 1} for item in metric_direction_response.values())

    def test_matches_internal(self, metric_direction_response: dict[str, int]) -> None:
        """Test that all the responses match what we use internally."""
        for key, value in metric_direction_response.items():
            assert value == MetricDirection[key]
