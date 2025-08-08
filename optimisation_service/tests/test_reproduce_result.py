import datetime
from uuid import UUID, uuid4

from app.internal.uuid7 import uuid7
from app.models.epoch_types.task_data_type import Building, Config, GasHeater, GasType, Grid, SolarPanel, TaskData
from app.models.simulate import ResultReproConfig
from app.models.site_data import FileLoc, RemoteMetaData


class TestResultReproConfig:
    def test_can_construct_uuid7(self) -> None:
        """Test that we can construct a ResultReproConfig with UUIDv7"""
        config = ResultReproConfig(
            portfolio_id=uuid7(),
            task_data={"demo_london": TaskData()},
            site_data={
                "demo_london": RemoteMetaData(
                    site_id="demo_london",
                    start_ts=datetime.datetime(year=2025, month=1, day=1, tzinfo=datetime.UTC),
                    end_ts=datetime.datetime(year=2025, month=2, day=1, tzinfo=datetime.UTC),
                    loc=FileLoc.remote,
                    HeatingLoad=[uuid7(), uuid7()],
                    ElectricityMeterData=uuid7(),
                )
            },
        )
        assert config
        config_json = config.model_dump_json()
        round_tripped = ResultReproConfig.model_validate_json(config_json)
        assert round_tripped == config

    def test_can_construct_uuid4(self) -> None:
        """Test that we can construct a ResultReproConfig with UUIDv7"""
        config = ResultReproConfig(
            portfolio_id=uuid4(),
            task_data={"demo_london": TaskData()},
            site_data={
                "demo_london": RemoteMetaData(
                    site_id="demo_london",
                    start_ts=datetime.datetime(year=2025, month=1, day=1, tzinfo=datetime.UTC),
                    end_ts=datetime.datetime(year=2025, month=2, day=1, tzinfo=datetime.UTC),
                    loc=FileLoc.remote,
                    HeatingLoad=[uuid4(), uuid4()],
                    ElectricityMeterData=uuid4(),
                )
            },
        )
        assert config
        config_json = config.model_dump_json()
        round_tripped = ResultReproConfig.model_validate_json(config_json)
        assert round_tripped == config

    def test_with_real_data(self) -> None:
        config = ResultReproConfig(
            portfolio_id=UUID("0ab3eb02-5df0-4d7f-af58-937e68dadf73"),
            task_data={
                "demo_london": TaskData(
                    building=Building(
                        scalar_heat_load=1.0,
                        scalar_electrical_load=1.0,
                        fabric_intervention_index=0,
                        incumbent=True,
                        age=0.0,
                        lifetime=30.0,
                    ),
                    data_centre=None,
                    domestic_hot_water=None,
                    electric_vehicles=None,
                    energy_storage_system=None,
                    gas_heater=GasHeater(
                        maximum_output=1000.0,
                        gas_type=GasType.NATURAL_GAS,
                        boiler_efficiency=0.9,
                        incumbent=True,
                        age=0.0,
                        lifetime=10.0,
                    ),
                    grid=Grid(
                        grid_export=1000.0,
                        grid_import=1000.0,
                        import_headroom=0.25,
                        tariff_index=0,
                        export_tariff=0.15,
                        incumbent=True,
                        age=0.0,
                        lifetime=25.0,
                    ),
                    heat_pump=None,
                    mop=None,
                    solar_panels=[SolarPanel(yield_scalar=5.0, yield_index=0, incumbent=False, age=0.0, lifetime=25.0)],
                    config=Config(
                        capex_limit=100000000.0,
                        use_boiler_upgrade_scheme=False,
                        general_grant_funding=0.0,
                        npv_time_horizon=10,
                        npv_discount_factor=0.0,
                    ),
                )
            },
            site_data={
                "demo_london": RemoteMetaData(
                    loc=FileLoc.remote,
                    site_id="demo_london",
                    start_ts=datetime.datetime(2022, 1, 1, 0, 0, tzinfo=datetime.UTC),
                    end_ts=datetime.datetime(2023, 1, 1, 0, 0, tzinfo=datetime.UTC),
                    SiteBaseline=None,
                    HeatingLoad=[
                        UUID("01983cac-d618-73fa-847a-a61ea5c92a19"),
                        UUID("01983cac-d618-73fa-847a-a61f3a5b4217"),
                        UUID("01983cac-d618-73fa-847a-a620ede48557"),
                        UUID("01983cac-d618-73fa-847a-a6219659ab00"),
                    ],
                    ASHPData=UUID("01983cba-b8a1-75fb-b4fe-d69ae1bf1fc2"),
                    CarbonIntensity=UUID("01983cac-d618-73fa-847a-a62296041e4a"),
                    ElectricityMeterData=UUID("a6462320-c50f-4dcc-a3f9-dbc0d972f1a4"),
                    ElectricityMeterDataSynthesised=UUID("01983cac-d61a-71c9-8f10-060fc78e6a48"),
                    ImportTariff=[
                        UUID("01983cac-d618-73fa-847a-a623608bbf6e"),
                        UUID("01983cac-d618-73fa-847a-a624259ec915"),
                        UUID("01983cac-d618-73fa-847a-a6264d7983f1"),
                        UUID("01983cac-d618-73fa-847a-a6250adcd0f8"),
                    ],
                    Weather=None,
                    GasMeterData=UUID("0c5d5024-2d8d-45c2-96e7-d10771bd63c7"),
                    RenewablesGeneration=[UUID("01983cac-d61a-71c9-8f10-060ed9d13607")],
                )
            },
        )
        assert config
