"""Tests for uploading and parsing of PHPP files via the endpoint."""

from typing import cast

import httpx
import pytest
import pytest_asyncio

type InterventionResponse = dict[str, dict[str, float | str]]


class TestListInterventions:
    """Test that we can list the suitable PHPP interventions."""

    @pytest_asyncio.fixture
    async def list_response(self, client: httpx.AsyncClient) -> InterventionResponse:
        """Get the JSON list of interventions from the endpoint."""
        resp = await client.post("/list-interventions")
        assert resp.status_code == 200, resp.text
        return cast(InterventionResponse, resp.json())

    def test_interventions_exist(self, list_response: InterventionResponse) -> None:
        """Test that we get interventions from the endpoint."""
        assert len(list_response) > 50

    def test_interventions_have_u_values(self, list_response: InterventionResponse) -> None:
        """Test that interventions have positive u values."""
        for name, value in list_response.items():
            assert "u_value" in value, "Item missing a U-value"
            assert value["u_value"] is None or isinstance(value["u_value"], float), f"Got wrong type for {name} u value"
            assert value["u_value"] is None or value["u_value"] > 0, f"Got a negative U-value for {name}"

    def test_interventions_have_costs(self, list_response: InterventionResponse) -> None:
        """Test that interventions have positive costs."""
        for name, value in list_response.items():
            assert "cost" in value, "Item missing a cost"
            assert value["cost"] is None or isinstance(value["cost"], float), f"Got wrong type for {name} cost"
            assert value["cost"] is None or value["cost"] > 0, f"Got a negative cost for {name}"


class TestUploadPHPP:
    """Test that we can upload a PHPP file."""

    @pytest.mark.asyncio
    async def test_upload_phpp(self, client: httpx.AsyncClient) -> None:
        """Test that we can upload a PHPP and get a good response."""
        with open("./data/phpp/PHPP_EN_V10.3_Retford Baseline.xlsx", "rb") as fi:
            resp = await client.post(
                "/upload-phpp",
                files={
                    "file": ("PHPP_EN_V10.3_Retford Baseline.xlsx", fi, "application/vnd.ms-excel"),
                },
                data={"site_id": "demo_london"},
            )
        assert resp.status_code == 200, resp.text

    @pytest.mark.asyncio
    async def test_can_list_phpp(self, client: httpx.AsyncClient) -> None:
        """Test that we can list the PHPPs added to the database."""
        # test that there are none to start
        resp = await client.post("/list-phpp", json={"site_id": "demo_london"})
        assert resp.status_code == 200
        assert not resp.json()

        with open("./data/phpp/PHPP_EN_V10.3_Retford Baseline.xlsx", "rb") as fi:
            resp = await client.post(
                "/upload-phpp",
                files={
                    "file": ("PHPP_EN_V10.3_Retford Baseline.xlsx", fi, "application/vnd.ms-excel"),
                },
                data={"site_id": "demo_london"},
            )
        assert resp.status_code == 200, resp.text

        resp = await client.post("/list-phpp", json={"site_id": "demo_london"})
        assert resp.status_code == 200
        listed_data = resp.json()
        assert len(listed_data) == 1
        assert listed_data[0]["filename"] == "PHPP_EN_V10.3_Retford Baseline.xlsx"
