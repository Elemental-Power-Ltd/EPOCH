from enum import StrEnum
from pathlib import Path
from typing import Literal, Self

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from app.models.database import dataset_id_t
from app.models.epoch_types.task_data_type import TaskData


class FileLoc(StrEnum):
    remote = "remote"
    local = "local"


class DataDuration(StrEnum):
    year = "year"


class SiteMetaData(BaseModel):
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

    # we mutate SiteMetaData requests (in hydrate_site_data_with_latest_dataset_ids)
    # so we validate assignment to prevent pydantic warnings about UUIDs vs Strings
    model_config = ConfigDict(validate_assignment=True)


class LocalMetaData(BaseModel):
    loc: Literal[FileLoc.local] = Field(
        examples=["local"], description="Location of data. Either in local directory or in remote database."
    )
    site_id: str = Field(
        examples=["demo_london"],
        description="The database ID for a site, all lower case, joined by underscores.",
    )
    path: Path = Field(examples=["./tests/data/benchmarks/var-3/InputData"], description="If a local file, the path to it.")


class EpochEntry(BaseModel):
    timestamps: list[AwareDatetime]


class FabricIntervention(BaseModel):
    cost: float
    reduced_hload: list[float]
    peak_hload: float = Field(description="Peak heating demand from a survey in kWth", default=0.0)


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
    peak_hload: float = 0.0
    ev_eload: list[float]
    dhw_demand: list[float]
    air_temperature: list[float]
    grid_co2: list[float]

    solar_yields: list[list[float]]
    import_tariffs: list[list[float]]
    fabric_interventions: list[FabricIntervention]

    ashp_input_table: list[list[float]]
    ashp_output_table: list[list[float]]

    @model_validator(mode="after")
    def validate_lengths(self) -> Self:
        """
        Check that the lengths of the site data are all the same, and return a helpful error message if not.

        A common failure pattern in the data service is to send blank arrays, or have some mismatching.
        This causes trouble further down in EPOCH, so reject the construction of the SiteData here by
        checking if any are zero or shorter than expected.
        The expected length is the maximum length we see, so you'll get a slightly odd message
        if one is too long.

        Parameters
        ----------
        self
            EpochSiteData to validate

        Returns
        -------
        Self
            If all lengths match

        Raises
        ------
        ValueError
            If any arrays are zero length, or shorter than expected.
        """
        lengths = {
            "building_eload": len(self.building_eload),
            "building_hload": len(self.building_hload),
            "ev_eload": len(self.building_eload),
            "dhw_demand": len(self.dhw_demand),
            "air_temperature": len(self.air_temperature),
            "grid_co2": len(self.grid_co2),
        }
        for idx, solar in enumerate(self.solar_yields):
            lengths[f"solar_{idx}"] = len(solar)
        for idx, tariff in enumerate(self.import_tariffs):
            lengths[f"tariff_{idx}"] = len(tariff)
        for idx, fabric in enumerate(self.fabric_interventions):
            lengths[f"fabric_{idx}"] = len(fabric.reduced_hload)

        all_nonzero = all(val > 0 for val in lengths.values())
        longest_len = max(lengths.values())
        all_same = all(val == longest_len for val in lengths.values())

        if all_nonzero and all_same:
            # We're all good!
            return self

        if not all_nonzero:
            zero_length_arrays = [key for key, val in lengths.items() if val == 0]
            raise ValueError(f"Got zero length arrays in EpochSiteData: {zero_length_arrays}")

        if not all_same:
            shorter_arrays = [(key, val) for key, val in lengths.items() if val < longest_len]
            raise ValueError(f"Got shorter length arrays in EpochSiteData: {shorter_arrays} but expected {longest_len}")
        raise ValueError(f"Problem with lengths in EpochSiteData: {lengths}")


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
    dataset_id: dataset_id_t
    dataset_type: DatasetTypeEnum
    created_at: AwareDatetime
