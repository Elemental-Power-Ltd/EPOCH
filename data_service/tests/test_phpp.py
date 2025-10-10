"""Test the internal implementation of the PHPP handling code."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.internal.thermal_model.phpp.interventions import StructuralArea
from app.internal.thermal_model.phpp.parse_phpp import (
    StructuralInfo,
    apply_phpp_intervention,
    phpp_fabric_heat_loss,
    phpp_fabric_intervention_cost,
    phpp_to_dataframe,
    phpp_total_heat_loss,
)


@pytest.fixture(scope="module")
def phpp_fpath() -> Path:
    """Load a PHPP into a dataframe and re-use it for each test."""
    return Path("tests", "data", "phpp", "PHPP_demo.xlsx").absolute()


@pytest.fixture(scope="module")
def parsed_phpp(phpp_fpath: Path) -> tuple[pd.DataFrame, StructuralInfo]:
    """Load a PHPP into a dataframe and re-use it for each test."""
    return phpp_to_dataframe(phpp_fpath)


class TestParsePHPP:
    """Test that we can parse PHPPs into python objects."""

    def test_retford_returns_ok(self, parsed_phpp: tuple[pd.DataFrame, StructuralInfo]) -> None:
        """Test that we can parse a PHPP for Retford town hall."""
        parsed_df = parsed_phpp[0]
        assert len(parsed_df) == 676, f"Wrong number of elements, expected 675 but got {len(parsed_df)}"

        assert not any(pd.isna(parsed_df["area"])), "Got NaN areas"
        assert not any(pd.isna(parsed_df["u_value"])), "Got NaN u_value"

    def test_has_windows_and_walls(self, parsed_phpp: tuple[pd.DataFrame, StructuralInfo]) -> None:
        """Test that we get windows and walls in each orientation."""
        parsed_df = parsed_phpp[0]
        assert any(parsed_df["name"].str.startswith("Wall")), "No walls found"
        assert any(parsed_df["name"].str.startswith("Win")), "No windows found"
        for orientation in ["N", "E", "S", "W"]:
            assert any(np.logical_and(parsed_df["name"].str.startswith("Wall"), parsed_df["name"].str.endswith(orientation))), (
                f"No Walls in orientation {orientation}"
            )
            assert any(np.logical_and(parsed_df["name"].str.startswith("Win"), parsed_df["name"].str.endswith(orientation))), (
                f"No Windows in orientation {orientation}"
            )

        assert (parsed_df["area_type"] == StructuralArea.ThermalBridge).any()

    def test_air_volume_correct(self, parsed_phpp: tuple[pd.DataFrame, StructuralInfo]) -> None:
        """Test that we get the correct air volume from the PHPP."""
        parsed_meta = parsed_phpp[1]
        assert parsed_meta["internal_volume"] == pytest.approx(4182, rel=1e-3), (
            f"Got wrong air volume: {parsed_meta['internal_volume']}"
        )

    def test_ach_correct(self, parsed_phpp: tuple[pd.DataFrame, StructuralInfo]) -> None:
        """Test that we get the correct air changes per hour from the PHPP."""
        parsed_meta = parsed_phpp[1]
        assert parsed_meta["air_changes"] == pytest.approx(10), "Got wrong ACH"


class TestHeatLoss:
    """Test some basic features of the heat loss."""

    def test_fabric_less_than_total(self, parsed_phpp: tuple[pd.DataFrame, StructuralInfo]) -> None:
        """Test that the fabric component is less than the total heat loss."""
        fabric_heat_loss = phpp_fabric_heat_loss(parsed_phpp[0])
        total_heat_loss = phpp_total_heat_loss(parsed_phpp[0], parsed_phpp[1])
        assert fabric_heat_loss < total_heat_loss


class TestHeatLossAndInterventions:
    """Test applying fabric interventions and their effect on heat loss."""

    @pytest.mark.parametrize(
        "intervention",
        [
            "Fineo Glazing",
            "External Insulation to external cavity wall",
            "Pitched Roof Insulation (between and under roof structure)",
        ],
    )
    def test_can_apply_intervention(self, parsed_phpp: tuple[pd.DataFrame, StructuralInfo], intervention: str) -> None:
        """Test that we can apply interventions to the PHPP to get new U values."""
        parsed_df = parsed_phpp[0]
        new_df = apply_phpp_intervention(parsed_df, intervention)
        assert new_df is not parsed_phpp, "Intervention dataframe didn't get copied"
        assert (new_df["u_value"] <= parsed_df["u_value"]).all(), "U values have increased"
        assert (new_df["u_value"] < parsed_df["u_value"]).any(), "U values have not lowered"

    def test_cant_apply_bad_intervention(self, parsed_phpp: tuple[pd.DataFrame, StructuralInfo]) -> None:
        """Test that we can't apply a bad intervention and get a helpful message."""
        parsed_df = parsed_phpp[0]
        with pytest.raises(ValueError, match="NOT_A_REAL_INTERVENTION"):
            apply_phpp_intervention(parsed_df, "NOT_A_REAL_INTERVENTION")

    @pytest.mark.parametrize(
        "intervention",
        [
            "Fineo Glazing",
            "External Insulation to external cavity wall",
            "Pitched Roof Insulation (between and under roof structure)",
        ],
    )
    def test_intervention_heatloss(self, parsed_phpp: tuple[pd.DataFrame, StructuralInfo], intervention: str) -> None:
        """Test that we can apply interventions to the PHPP to get a lower heat loss."""
        parsed_df = parsed_phpp[0]
        new_df = apply_phpp_intervention(parsed_df, intervention)
        assert phpp_fabric_heat_loss(new_df) < phpp_fabric_heat_loss(parsed_df)


class TestFabricCostBreakdown:
    """Test that we compute the cost and breakdown sensibly."""

    def test_order_independent(self, parsed_phpp: tuple[pd.DataFrame, StructuralInfo]) -> None:
        """Test that we don't care about the order of fabric interventions."""
        parsed_df = parsed_phpp[0]
        interventions = ["Fineo Glazing", "Secondary Glazing"]
        cost_1, breakdown_1 = phpp_fabric_intervention_cost(parsed_df, interventions)
        cost_2, breakdown_2 = phpp_fabric_intervention_cost(parsed_df, interventions[::-1])

        assert cost_1 == cost_2
        assert breakdown_1[1] == breakdown_2[0]
        assert breakdown_1[0] == breakdown_2[1]

    def test_worse_not_cheaper(self, parsed_phpp: tuple[pd.DataFrame, StructuralInfo]) -> None:
        """Test that overwriting with a worse intervention doesn't save money."""
        parsed_df = parsed_phpp[0]
        interventions = ["Fineo Glazing", "Secondary Glazing"]
        cost_1, breakdown_1 = phpp_fabric_intervention_cost(parsed_df, [interventions[0]])
        cost_2, breakdown_2 = phpp_fabric_intervention_cost(parsed_df, interventions)

        assert cost_1 == cost_2
        assert breakdown_1[0] == breakdown_2[0]
        assert breakdown_2[1].area == 0.0

    def test_non_u_value_costed(self, parsed_phpp: tuple[pd.DataFrame, StructuralInfo]) -> None:
        """Test that overwriting with a worse intervention doesn't save money."""
        parsed_df = parsed_phpp[0]
        interventions = ["Air tightness to external voids and penetrations"]
        cost, breakdown = phpp_fabric_intervention_cost(parsed_df, interventions)

        assert cost > 0
        assert breakdown[0].area != 0.0
        assert breakdown[0].cost == cost