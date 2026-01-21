"""Test we can add, list and retrieve cost models."""

from typing import Any

import httpx
import pytest

from app.internal.utils.uuid import uuid7


@pytest.fixture
def cost_model() -> dict[str, Any]:
    """Return the default ALCHEMAI cost model."""
    return {
        "capex_model": {
            "dhw_prices": {
                "fixed_cost": 1000,
                "segments": [{"upper": 300, "rate": 6.5}, {"upper": 800, "rate": 5}],
                "final_rate": 3,
            },
            "gas_heater_prices": {
                "fixed_cost": 1000,
                "segments": [{"upper": 100, "rate": 250}, {"upper": 200, "rate": 225}],
                "final_rate": 200,
            },
            "grid_prices": {
                "fixed_cost": 0,
                "segments": [{"upper": 50, "rate": 240}, {"upper": 1000, "rate": 160}],
                "final_rate": 120,
            },
            "heatpump_prices": {
                "fixed_cost": 4000,
                "segments": [{"upper": 15, "rate": 800}, {"upper": 100, "rate": 2500}],
                "final_rate": 1500,
            },
            "ess_pcs_prices": {
                "fixed_cost": 0,
                "segments": [{"upper": 50, "rate": 250}, {"upper": 1000, "rate": 125}],
                "final_rate": 75,
            },
            "ess_enclosure_prices": {
                "fixed_cost": 0,
                "segments": [{"upper": 100, "rate": 480}, {"upper": 2000, "rate": 360}],
                "final_rate": 300,
            },
            "ess_enclosure_disposal_prices": {
                "fixed_cost": 0,
                "segments": [{"upper": 100, "rate": 30}, {"upper": 2000, "rate": 20}],
                "final_rate": 15,
            },
            "pv_panel_prices": {
                "fixed_cost": 0,
                "segments": [{"upper": 50, "rate": 150}, {"upper": 1000, "rate": 110}],
                "final_rate": 95,
            },
            "pv_roof_prices": {
                "fixed_cost": 4250,
                "segments": [{"upper": 50, "rate": 850}, {"upper": 1000, "rate": 750}],
                "final_rate": 600,
            },
            "pv_ground_prices": {
                "fixed_cost": 4250,
                "segments": [{"upper": 50, "rate": 800}, {"upper": 1000, "rate": 600}],
                "final_rate": 500,
            },
            "pv_BoP_prices": {
                "fixed_cost": 0,
                "segments": [{"upper": 50, "rate": 120}, {"upper": 1000, "rate": 88}],
                "final_rate": 76,
            },
        },
        "opex_model": {
            "ess_pcs_prices": {
                "fixed_cost": 0,
                "segments": [{"upper": 50, "rate": 8}, {"upper": 1000, "rate": 4}],
                "final_rate": 1,
            },
            "ess_enclosure_prices": {
                "fixed_cost": 0,
                "segments": [{"upper": 100, "rate": 10}, {"upper": 2000, "rate": 4}],
                "final_rate": 2,
            },
            "gas_heater_prices": {"fixed_cost": 0, "segments": [], "final_rate": 0},
            "heatpump_prices": {"fixed_cost": 0, "segments": [], "final_rate": 0},
            "pv_prices": {
                "fixed_cost": 0,
                "segments": [{"upper": 50, "rate": 2}, {"upper": 1000, "rate": 1}],
                "final_rate": 0.5,
            },
        },
    }


class TestCostModels:
    """Tests for the cost models."""

    @pytest.mark.asyncio
    async def test_add_and_retrieve_cost_model(self, client: httpx.AsyncClient, cost_model: dict[str, Any]) -> None:
        """Add a cost model and then check we can retrieve it."""
        add_response = await client.post(
            "/add-cost-model",
            json={
                "model_name": "test_model",
                "capex_model": cost_model["capex_model"],
                "opex_model": cost_model["opex_model"],
            },
        )

        assert add_response.is_success, add_response.text

        model_id = add_response.json()["cost_model_id"]
        assert model_id != "", "cost_model_id not generated"

        get_response = await client.post(f"/get-cost-model?cost_model_id={model_id}")

        assert get_response.is_success, get_response.text
        returned_model = get_response.json()

        assert returned_model["model_name"] == "test_model"
        assert returned_model["capex_model"] == cost_model["capex_model"]

    @pytest.mark.asyncio
    async def test_list_cost_models(self, client: httpx.AsyncClient, cost_model: dict[str, Any]) -> None:
        """Add two cost models and check they are returned by creation date."""
        first_response = await client.post(
            "/add-cost-model",
            json={
                "model_name": "first_model",
                "capex_model": cost_model["capex_model"],
                "opex_model": cost_model["opex_model"],
            },
        )

        assert first_response.is_success, first_response.text

        second_response = await client.post(
            "/add-cost-model",
            json={
                "model_name": "second_model",
                "capex_model": cost_model["capex_model"],
                "opex_model": cost_model["opex_model"],
            },
        )

        assert second_response.is_success, second_response.text

        list_response = await client.post("/list-cost-models")
        assert list_response.is_success, list_response.text

        models = list_response.json()
        assert len(models) == 2

        assert models[0]["model_name"] == "first_model"
        assert models[1]["model_name"] == "second_model"

    @pytest.mark.asyncio
    async def test_get_cost_model_bad_id(self, client: httpx.AsyncClient) -> None:
        """Check we get an error when requesting with an invalid ID."""
        bad_id = uuid7()

        get_resp = await client.post(f"/get-cost-model?cost_model_id={bad_id}")

        assert get_resp.is_client_error, get_resp.text
