from app.internal.site_range import count_parameters_to_optimise
from app.models.site_range import Building, Config, HeatPump, HeatSourceEnum, Renewables, SiteRange


class Test_count_parameters_to_optimise:
    def test_COMPONENT_IS_MANDATORY(self):
        building = Building(
            COMPONENT_IS_MANDATORY=True, scalar_heat_load=[1.0], scalar_electrical_load=[1.0], fabric_intervention_index=[0]
        )
        renewables = Renewables(COMPONENT_IS_MANDATORY=False, yield_scalars=[[1]])
        heat_pump = HeatPump(
            COMPONENT_IS_MANDATORY=False, heat_power=[1], heat_source=[HeatSourceEnum.AMBIENT_AIR], send_temp=[2.0]
        )
        config = Config(capex_limit=9999999999)

        site_range = SiteRange(building=building, renewables=renewables, heat_pump=heat_pump, config=config)

        assert count_parameters_to_optimise(site_range) == 2

    def test_asset_values(self):
        building = Building(
            COMPONENT_IS_MANDATORY=True,
            scalar_heat_load=[1.0],
            scalar_electrical_load=[1.0],
            fabric_intervention_index=[0, 1],
        )
        renewables = Renewables(COMPONENT_IS_MANDATORY=True, yield_scalars=[[1, 2], [1, 2]])
        heat_pump = HeatPump(
            COMPONENT_IS_MANDATORY=True,
            heat_power=[1, 2],
            heat_source=[HeatSourceEnum.AMBIENT_AIR, HeatSourceEnum.HOTROOM],
            send_temp=[2.0],
        )
        config = Config(capex_limit=9999999999)

        site_range = SiteRange(building=building, renewables=renewables, heat_pump=heat_pump, config=config)

        assert count_parameters_to_optimise(site_range) == 5
