import pytest
from pydantic import ValidationError

from app.internal.site_range import count_parameters_in_asset, count_parameters_to_optimise
from app.models.core import Site
from app.models.epoch_types.site_range_type import Building, HeatPump, HeatSourceEnum, SiteRange, SolarPanel


class TestCountParametersToOptimise:
    def test_COMPONENT_IS_MANDATORY(self) -> None:
        building = Building(
            COMPONENT_IS_MANDATORY=True,
            scalar_heat_load=[1.0],
            scalar_electrical_load=[1.0],
            fabric_intervention_index=[0],
            incumbent=False,
            age=0,
            lifetime=30,
        )
        panel_1 = SolarPanel(
            COMPONENT_IS_MANDATORY=False, yield_scalar=[1], yield_index=[0], incumbent=False, age=0, lifetime=25
        )
        panel_2 = SolarPanel(
            COMPONENT_IS_MANDATORY=True, yield_scalar=[1], yield_index=[0], incumbent=False, age=0, lifetime=25
        )
        heat_pump = HeatPump(
            COMPONENT_IS_MANDATORY=False,
            heat_power=[1],
            heat_source=[HeatSourceEnum.AMBIENT_AIR],
            send_temp=[2.0],
            incumbent=False,
            age=0,
            lifetime=10,
        )

        site_range = SiteRange(building=building, solar_panels=[panel_1, panel_2], heat_pump=heat_pump)

        assert count_parameters_to_optimise(site_range) == 2

    def test_asset_values(self) -> None:
        building = Building(
            COMPONENT_IS_MANDATORY=True,
            scalar_heat_load=[1.0],
            scalar_electrical_load=[1.0],
            fabric_intervention_index=[0, 1],
            incumbent=False,
            age=0,
            lifetime=30,
        )
        panel_1 = SolarPanel(
            COMPONENT_IS_MANDATORY=True, yield_scalar=[1], yield_index=[0, 2], incumbent=False, age=0, lifetime=25
        )
        panel_2 = SolarPanel(
            COMPONENT_IS_MANDATORY=False, yield_scalar=[1, 2], yield_index=[0], incumbent=False, age=0, lifetime=25
        )
        heat_pump = HeatPump(
            COMPONENT_IS_MANDATORY=True,
            heat_power=[1, 2],
            heat_source=[HeatSourceEnum.AMBIENT_AIR, HeatSourceEnum.HOTROOM],
            send_temp=[2.0],
            incumbent=False,
            age=0,
            lifetime=10,
        )

        site_range = SiteRange(building=building, solar_panels=[panel_1, panel_2], heat_pump=heat_pump)

        assert count_parameters_to_optimise(site_range) == 6


class TestCountParametersInAsset:
    def test_COMPONENT_IS_MANDATORY(self) -> None:
        mandatory_building = Building(
            COMPONENT_IS_MANDATORY=True,
            scalar_heat_load=[1.0],
            scalar_electrical_load=[1.0],
            fabric_intervention_index=[0],
            incumbent=False,
            age=0,
            lifetime=30,
        )

        optional_building = Building(
            COMPONENT_IS_MANDATORY=False,
            scalar_heat_load=[1.0],
            scalar_electrical_load=[1.0],
            fabric_intervention_index=[0],
            incumbent=False,
            age=0,
            lifetime=30,
        )

        assert count_parameters_in_asset(mandatory_building.model_dump()) == 0
        assert count_parameters_in_asset(optional_building.model_dump()) == 1

    def test_asset_values(self) -> None:
        heat_pump = HeatPump(
            COMPONENT_IS_MANDATORY=False,
            heat_power=[1],
            heat_source=[HeatSourceEnum.AMBIENT_AIR, HeatSourceEnum.HOTROOM],
            send_temp=[2.0, 3.0],
            incumbent=False,
            age=0,
            lifetime=10,
        )

        # 3 varying parameters: COMPONENT_IS_MANDATORY, heat_source, send_temp
        # 1 fixed parameter: heat_power
        assert count_parameters_in_asset(heat_pump.model_dump()) == 3


class TestSiteIndices:
    """Test that we regret site data/range setups where the requested indices are out of range."""

    def test_index_all_good(self, default_site: Site) -> None:
        """Test that with a reasonable default fabric index we're fine"""
        assert default_site

    def test_tariff_wrong(self, default_site: Site) -> None:
        """Test that we fail if there's a bad tariff index."""
        bad_site = default_site.model_copy(deep=True)
        assert bad_site.site_range.grid is not None
        bad_site.site_range.grid.tariff_index = [0, 1, 2, 3, 4, 5]
        with pytest.raises(ValidationError, match="tariff_index"):
            Site.model_validate(bad_site)

    def test_fabric_wrong(self, default_site: Site) -> None:
        """Test that we fail if there's a bad fabric index."""
        bad_site = default_site.model_copy(deep=True)
        assert bad_site.site_range.building is not None
        bad_site.site_range.building.fabric_intervention_index = [0, 1, 2, 3, 4, 5]
        with pytest.raises(ValidationError, match="fabric_index"):
            Site.model_validate(bad_site)
