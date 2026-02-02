import datetime

import pytest
from app.models.site_data import EpochSiteData
from pydantic import ValidationError


class TestSiteDataLength:
    """Test that the length checkers for site data work."""

    def test_all_same_okay(self, default_epoch_data: EpochSiteData) -> None:
        """Test that we've constructed an object with good data."""
        assert default_epoch_data

    def test_bad_shorter(self, default_epoch_data: EpochSiteData) -> None:
        """Test that we complain if there's a shorter entry."""
        bad_epoch_data = default_epoch_data.model_copy()
        bad_epoch_data.air_temperature.pop()
        with pytest.raises(ValidationError, match="air_temperature"):
            EpochSiteData.model_validate(bad_epoch_data)

    def test_bad_longer(self, default_epoch_data: EpochSiteData) -> None:
        """Test that we complain if there's a longer entry."""
        bad_epoch_data = default_epoch_data.model_copy()
        bad_epoch_data.air_temperature.append(1)
        with pytest.raises(ValidationError):
            EpochSiteData.model_validate(bad_epoch_data)

    def test_bad_single_zero(self, default_epoch_data: EpochSiteData) -> None:
        """Test that we complain if there's a single zero length entry."""
        bad_epoch_data = default_epoch_data.model_copy()
        bad_epoch_data.air_temperature = []
        with pytest.raises(ValidationError, match="air_temperature"):
            EpochSiteData.model_validate(bad_epoch_data)

    def test_bad_all_zero(self, default_epoch_data: EpochSiteData) -> None:
        """Test that we complain if there's all zero length entries."""
        expected = "['building_eload', 'building_hload', 'ev_eload', 'dhw_demand', 'air_temperature', 'grid_co2']"
        with pytest.raises(ValidationError, match=expected):
            EpochSiteData(
                start_ts=datetime.datetime(year=2022, month=1, day=1, tzinfo=datetime.UTC),
                end_ts=datetime.datetime(year=2023, month=1, day=1, tzinfo=datetime.UTC),
                baseline=default_epoch_data.baseline,
                building_eload=[],
                building_hload=[],
                peak_hload=0.0,
                ev_eload=[],
                dhw_demand=[],
                air_temperature=[],
                grid_co2=[],
                solar_yields=[],
                import_tariffs=[],
                fabric_interventions=[],
                ashp_input_table=[[]],
                ashp_output_table=[[]],
            )
