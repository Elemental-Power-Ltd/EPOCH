from app.internal.heuristics.asset_heuristics import EnergyStorageSystem, HeatPump, Renewables
from app.models.core import Site


class TestHeatPump:
    def test_heat_power(self, default_site: Site):
        epoch_data = default_site._epoch_data
        N = len(epoch_data.building_eload)
        timestamps = [epoch_data.start_ts + (epoch_data.end_ts - epoch_data.start_ts) * i / (N - 1) for i in range(N)]
        HeatPump.heat_power(
            building_hload=epoch_data.building_hload,
            ashp_input_table=epoch_data.ashp_input_table,
            ashp_output_table=epoch_data.ashp_output_table,
            air_temperature=epoch_data.air_temperature,
            timestamps=timestamps,
            ashp_mode=2.0,
        )


class TestRenewables:
    def test_yield_scalars(self, default_site: Site):
        epoch_data = default_site._epoch_data
        Renewables.yield_scalars(
            solar_yield=epoch_data.solar_yields[0],
            building_eload=epoch_data.building_eload,
        )


class TestEnergyStorageSystem:
    def test_capacity(self, default_site: Site):
        epoch_data = default_site._epoch_data
        N = len(epoch_data.building_eload)
        timestamps = [epoch_data.start_ts + (epoch_data.end_ts - epoch_data.start_ts) * i / (N - 1) for i in range(N)]
        EnergyStorageSystem.capacity(building_eload=epoch_data.building_eload, timestamps=timestamps)

    def test_ccharge_power(self, default_site: Site):
        epoch_data = default_site._epoch_data
        N = len(epoch_data.building_eload)
        timestamps = [epoch_data.start_ts + (epoch_data.end_ts - epoch_data.start_ts) * i / (N - 1) for i in range(N)]
        solar_scale = Renewables.yield_scalars(
            solar_yield=epoch_data.solar_yields[0],
            building_eload=epoch_data.building_eload,
        )
        EnergyStorageSystem.charge_power(solar_yield=epoch_data.solar_yields[0], timestamps=timestamps, solar_scale=solar_scale)

    def test_discharge_power(self, default_site: Site):
        epoch_data = default_site._epoch_data
        N = len(epoch_data.building_eload)
        timestamps = [epoch_data.start_ts + (epoch_data.end_ts - epoch_data.start_ts) * i / (N - 1) for i in range(N)]
        EnergyStorageSystem.discharge_power(building_eload=epoch_data.building_eload, timestamps=timestamps)
