"""Test the internal implementation of the PHPP handling code."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.internal.thermal_model.phpp.interventions import StructuralArea
from app.internal.thermal_model.phpp.parse_phpp import apply_phpp_intervention, phpp_fabric_heat_loss, phpp_to_dataframe


@pytest.fixture(scope="module")
def parsed_phpp() -> pd.DataFrame:
    """Load a PHPP into a dataframe and re-use it for each test."""
    fpath = Path("tests", "data", "phpp", "PHPP_EN_V10.3_Retford Baseline.xlsx").absolute()
    return phpp_to_dataframe(fpath)[0]


class TestParsePHPP:
    """Test that we can parse PHPPs into python objects."""

    def test_retford_returns_ok(self, parsed_phpp: pd.DataFrame) -> None:
        """Test that we can parse a PHPP for Retford town hall."""
        assert len(parsed_phpp) == 676, f"Wrong number of elements, expected 675 but got {len(parsed_phpp)}"

        assert not any(pd.isna(parsed_phpp["area"])), "Got NaN areas"
        assert not any(pd.isna(parsed_phpp["u_value"])), "Got NaN u_value"

    def test_has_windows_and_walls(self, parsed_phpp: pd.DataFrame) -> None:
        """Test that we get windows and walls in each orientation."""
        assert any(parsed_phpp["name"].str.startswith("Wall")), "No walls found"
        assert any(parsed_phpp["name"].str.startswith("Win")), "No windows found"
        for orientation in ["N", "E", "S", "W"]:
            assert any(
                np.logical_and(parsed_phpp["name"].str.startswith("Wall"), parsed_phpp["name"].str.endswith(orientation))
            ), f"No Walls in orientation {orientation}"
            assert any(
                np.logical_and(parsed_phpp["name"].str.startswith("Win"), parsed_phpp["name"].str.endswith(orientation))
            ), f"No Windows in orientation {orientation}"

        assert (parsed_phpp["area_type"] == StructuralArea.ThermalBridge).any()


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
    def test_can_apply_intervention(self, parsed_phpp: pd.DataFrame, intervention: str) -> None:
        """Test that we can apply interventions to the PHPP to get new U values."""
        new_df = apply_phpp_intervention(parsed_phpp, intervention)
        assert new_df is not parsed_phpp, "Intervention dataframe didn't get copied"
        assert (new_df["u_value"] <= parsed_phpp["u_value"]).all(), "U values have increased"
        assert (new_df["u_value"] < parsed_phpp["u_value"]).any(), "U values have not lowered"

    def test_cant_apply_bad_intervention(self, parsed_phpp: pd.DataFrame) -> None:
        """Test that we can't apply a bad intervention and get a helpful message."""
        with pytest.raises(ValueError, match="NOT_A_REAL_INTERVENTION"):
            apply_phpp_intervention(parsed_phpp, "NOT_A_REAL_INTERVENTION")

    @pytest.mark.parametrize(
        "intervention",
        [
            "Fineo Glazing",
            "External Insulation to external cavity wall",
            "Pitched Roof Insulation (between and under roof structure)",
        ],
    )
    def test_intervention_heatloss(self, parsed_phpp: pd.DataFrame, intervention: str) -> None:
        """Test that we can apply interventions to the PHPP to get a lower heat loss."""
        new_df = apply_phpp_intervention(parsed_phpp, intervention)
        assert phpp_fabric_heat_loss(new_df) < phpp_fabric_heat_loss(parsed_phpp)
