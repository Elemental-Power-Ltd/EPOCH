from enum import StrEnum
from os import PathLike
from typing import Annotated, Literal

from pydantic import UUID4, AwareDatetime, BaseModel, Field

from app.models.epoch_types.task_data_type import TaskData


class FileLoc(StrEnum):
    remote = "remote"
    local = "local"


class DataDuration(StrEnum):
    year = "year"


dataset_id_t = Annotated[UUID4, "String serialised UUID"]


class RemoteMetaData(BaseModel):
    loc: Literal[FileLoc.remote] = Field(
        examples=["remote"], description="Location of data. Either in local directory or in remote database."
    )
    site_id: str = Field(
        examples=["demo_london"],
        description="The database ID for a site, all lower case, joined by underscores.",
    )
    start_ts: AwareDatetime = Field(
        examples=["2022-01-01T00:00:00Z"],
        description="The earliest time (inclusive) to retrieve data for.",
    )
    end_ts: AwareDatetime = Field(
        examples=["2023-01-01T00:00:00Z"],
        description="The latest time (exclusive) to retrieve data for.",
    )
    SiteBaseline: dataset_id_t | None = Field(default=None)
    HeatingLoad: dataset_id_t | list[dataset_id_t] | None = Field(default=None)
    ASHPData: dataset_id_t | None = Field(default=None)
    CarbonIntensity: dataset_id_t | None = Field(default=None)
    ElectricityMeterData: dataset_id_t | None = Field(default=None)
    ElectricityMeterDataSynthesised: dataset_id_t | None = Field(default=None)
    ImportTariff: dataset_id_t | list[dataset_id_t] | None = Field(default=None)
    Weather: dataset_id_t | None = Field(default=None)
    GasMeterData: dataset_id_t | None = Field(default=None)
    RenewablesGeneration: dataset_id_t | list[dataset_id_t] | None = Field(default=None)


class LocalMetaData(BaseModel):
    loc: Literal[FileLoc.local] = Field(
        examples=["local"], description="Location of data. Either in local directory or in remote database."
    )
    site_id: str = Field(
        examples=["demo_london"],
        description="The database ID for a site, all lower case, joined by underscores.",
    )
    path: PathLike = Field(examples=["./tests/data/benchmarks/var-3/InputData"], description="If a local file, the path to it.")


class EpochEntry(BaseModel):
    timestamps: list[AwareDatetime]


class FabricIntervention(BaseModel):
    cost: float
    reduced_hload: list[float]
    peak_hload: float = Field(
        description="Peak heating demand from a survey in kWth", default_factory=lambda data: max(data["reduced_hload"])
    )


class EpochHeatingEntry(EpochEntry):
    data: list[FabricIntervention] = Field(
        examples=[[0.123, 4.56]],
        description="List of heating loads representing various fabric interventions with corresponding cost.",
    )


class EpochAirTempEntry(EpochEntry):
    data: list[float] = Field(examples=[[16.0, 15.5, 15.0, 14.7]], description="Air temperature for this time period in °C.")


class EpochDHWEntry(EpochEntry):
    data: list[float] = Field(examples=[[0.123, 4.56]], description="Domestic hot water demand in kWh for this time period.")


class ASHPCOPResponse(BaseModel):
    data: list[list[float]] = Field(
        examples=[
            [
                [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 40.0, 50.0, 60.0, 70.0],
                [-15.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.99, 1.0, 1.0, 1.0],
                [-10.0, 1.0, 1.0, 1.0, 0.99, 0.99, 1.0, 0.96, 0.99, 1.0, 0.96],
            ]
        ],
        description="""
        Row major ASHP lookup table.
        First element of each row should be the row's index: the Ambient air temperatures in °C for COP lookup.
        First row should be column headers: Output (send) hot water temperature in °C for COP lookup.
        """,
    )


class EpochElectricityEntry(EpochEntry):
    data: list[float] = Field(examples=[[0.123, 4.56]], description="List of fixed electrical loads for this building in kWh.")


class EpochTariffEntry(EpochEntry):
    data: list[list[float]] = Field(
        examples=[[[32.4, 14.6], [16.3, 20.8]]],
        description="List of import tariffs. Each import tariff is a list of Import costs for this time period in £ / kWh.",
    )


class EpochRenewablesEntry(EpochEntry):
    data: list[list[float]] = Field(
        examples=[[0.123, 4.56], [5.4, 6.7]],
        description="""A list of renewable array generations.
        Each renewable array generation is a list of renewable generations in kW / kWp for this array for this time period.""",
    )


class EpochCarbonEntry(EpochEntry):
    data: list[float] = Field(
        examples=[[32.4, 14.6, 7.2, 13.3]], description="List of carbon intensities during this time period in g CO2 / kWh."
    )


class SiteDataEntries(BaseModel):
    baseline: TaskData
    dhw: EpochDHWEntry
    air_temp: EpochAirTempEntry
    eload: EpochElectricityEntry
    heat: EpochHeatingEntry
    rgen: EpochRenewablesEntry
    import_tariffs: EpochTariffEntry
    grid_co2: EpochCarbonEntry

    ashp_input: ASHPCOPResponse
    ashp_output: ASHPCOPResponse


class EpochSiteData(BaseModel):
    start_ts: AwareDatetime
    end_ts: AwareDatetime

    baseline: TaskData

    building_eload: list[float]
    building_hload: list[float]
    peak_hload: float
    ev_eload: list[float]
    dhw_demand: list[float]
    air_temperature: list[float]
    grid_co2: list[float]

    solar_yields: list[list[float]]
    import_tariffs: list[list[float]]
    fabric_interventions: list[FabricIntervention]

    ashp_input_table: list[list[float]]
    ashp_output_table: list[list[float]]


SiteMetaData = RemoteMetaData | LocalMetaData


class DatasetTypeEnum(StrEnum):
    SiteBaseline = "SiteBaseline"
    GasMeterData = "GasMeterData"
    ElectricityMeterData = "ElectricityMeterData"
    ElectricityMeterDataSynthesised = "ElectricityMeterDataSynthesised"
    RenewablesGeneration = "RenewablesGeneration"
    Weather = "Weather"
    CarbonIntensity = "CarbonIntensity"
    HeatingLoad = "HeatingLoad"
    ASHPData = "ASHPData"
    ImportTariff = "ImportTariff"


class DatasetEntry(BaseModel):
    dataset_id: UUID4
    dataset_type: DatasetTypeEnum
    created_at: AwareDatetime
