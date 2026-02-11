from __future__ import annotations

import math
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.internal_models import PydanticTaskData


class PanelInfo(BaseModel):
    solar_peak: float = Field(ge=0.0)
    direction: Literal["North", "East", "South", "West"]  # Chose one of the four solar data arrays


class HeatInfo(BaseModel):
    heat_power: float = Field(gt=0.0)
    heat_source: Literal["Boiler", "HeatPump"]


class InsulationInfo(BaseModel):
    double_glazing: bool
    cladding: bool
    loft: bool


class BatteryInfo(BaseModel):
    capacity: float = Field(gt=0.0)
    power: float = Field(gt=0.0)


Location = Literal["Cardiff", "London", "Edinburgh"]
BuildingType = Literal["Domestic", "TownHall", "LeisureCentre"]


class SimulationRequest(BaseModel):
    # SiteData configuration
    location: Location
    building: BuildingType

    # TaskData configuration
    panels: list[PanelInfo]
    heat: HeatInfo
    insulation: InsulationInfo
    battery: BatteryInfo | None

    # Result configuration
    full_reporting: bool = False


class DemoResult(BaseModel):
    metrics: SimulationMetrics
    task_data: PydanticTaskData
    site_data: dict[str, Any] | None
    report_data: ReportData | None
    days_of_interest: list[Any]


# the following type definitions are copied directly from the optimisation_service
# this is to coerce the response into something our gui understands


class Grade(StrEnum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"


class SimulationMetrics(BaseModel):
    """Metrics for a site or portfolio of sites."""

    meter_balance: float | None = Field(
        description="Monetary savings from importing and exporting fuel/electricity when compared against the baseline.",
        default=None,
    )
    operating_balance: float | None = Field(
        description="Monetary savings from fuel, electricity and opex when compared against the baseline.", default=None
    )
    cost_balance: float | None = Field(
        description="Monetary savings from fuel, electricity, opex and annualised cost when compared against the baseline.",
        default=None,
    )
    npv_balance: float | None = Field(
        description="The change in Net Present Value between the baseline and the scenario.", default=None
    )
    payback_horizon: float | None = Field(
        description="Years for this scenario to pay back (if very large, represents no payback ever.)",
        default=None,
    )
    return_on_investment: float | None = Field(
        description="Yearly return on investment (operating balance / capex) as a decimal percentage. "
                    + "None when no money was spent.",
        default=None,
    )
    carbon_balance_scope_1: float | None = Field(
        description="Direct carbon emissions saved by this scenario.", default=None, examples=[None, math.pi]
    )
    carbon_balance_scope_2: float | None = Field(
        description="Net kg CO2e over the lifetime of these interventions for scope 2.", default=None
    )
    carbon_balance_total: float | None = Field(
        description="Net kg CO2e saved from both scope 1 and scope 2 emissions",
        default=None,
    )
    carbon_cost: float | None = Field(description="Net £ per t CO2e over the lifetime of these interventions.",
                                      default=None)
    total_gas_used: float | None = Field(description="Total gas imported (kWh).", default=None)
    total_electricity_imported: float | None = Field(
        description="Total electricity imported from the grid (kWh).", default=None
    )
    total_electricity_generated: float | None = Field(description="Total electricity generated on-site (kWh).",
                                                      default=None)
    total_electricity_exported: float | None = Field(description="Total electricity exported to the grid (kWh).",
                                                     default=None)
    total_electricity_curtailed: float | None = Field(
        description="Total electricity surplus that could not be exported (kWh).", default=None
    )
    total_electricity_used: float | None = Field(description="Total electricity used (kWh).", default=None)
    total_electrical_shortfall: float | None = Field(
        description="Total electrical shortfall (kWh) when compared to the demand.", default=None
    )
    total_heat_load: float | None = Field(description="Total heat used (kWh).", default=None)
    total_dhw_load: float | None = Field(description="Total heat used for domestic hot water (kWh).", default=None)
    total_ch_load: float | None = Field(description="Total heat used for central heating (kWh).", default=None)
    total_heat_shortfall: float | None = Field(
        description="Total heat shortfall (kWh) when compared to the demand.", default=None
    )
    total_ch_shortfall: float | None = Field(
        description="Total central heating (CH) shortfall (kWh) when compared to the demand.", default=None
    )
    total_dhw_shortfall: float | None = Field(
        description="Total domestic hot water (DHW) shortfall (kWh) when compared to the demand.", default=None
    )
    peak_hload_shortfall: float | None = Field(
        description="Shortfall in meeting the peak heating demand calculated by an external source (such as PHPP)",
        default=None
    )
    capex: float | None = Field(description="Cost to install this scenario.", default=None)
    total_gas_import_cost: float | None = Field(description="Total spend (£) importing gas.", default=None)
    total_electricity_import_cost: float | None = Field(
        description="Total spend (£) importing electricity from the grid.", default=None
    )
    total_electricity_export_gain: float | None = Field(
        description="Total income (£) exporting electricity to this grid.", default=None
    )

    total_meter_cost: float | None = Field(
        description="Total cost of importing fuel/electricity minus revenue from exporting.", default=None
    )
    total_operating_cost: float | None = Field(
        description="Total meter cost minus operating costs for components.", default=None
    )
    annualised_cost: float | None = Field(
        description="Cost of running this scenario (including amortised deprecation).", default=None
    )
    total_net_present_value: float | None = Field(
        description="Net Present Value after repeating the simulation for the configured number of years.",
        default=None,
    )
    total_scope_1_emissions: float | None = Field(description="Total Scope 1 emissions (kg CO2e).", default=None)
    total_scope_2_emissions: float | None = Field(description="Total Scope 2 emissions (kg CO2e).", default=None)
    total_combined_carbon_emissions: float | None = Field(description="Scope 1 and Scope 2 emissions (kg CO2e).",
                                                          default=None)

    scenario_environmental_impact_score: int | None = Field(description="environmental impact score based on SAP",
                                                            default=None)
    scenario_environmental_impact_grade: Grade | None = Field(description="environmental impact grade (A-G)",
                                                              default=None)
    scenario_capex_breakdown: list[CostInfo] | None = Field(description="Breakdown of scenario expenditure.",
                                                            default=None)

    baseline_gas_used: float | None = Field(description="Baseline gas imported (kWh).", default=None)
    baseline_electricity_imported: float | None = Field(
        description="Baseline electricity imported from the grid (kWh).", default=None
    )
    baseline_electricity_generated: float | None = Field(
        description="Baseline electricity generated on-site (kWh).", default=None
    )
    baseline_electricity_exported: float | None = Field(
        description="Baseline electricity exported to the grid (kWh).", default=None
    )
    baseline_electricity_curtailed: float | None = Field(
        description="Baseline electricity surplus that could not be exported (kWh).", default=None
    )
    baseline_electricity_used: float | None = Field(description="Baseline electricity used (kWh).", default=None)

    baseline_electrical_shortfall: float | None = Field(
        description="Baseline electrical shortfall (kWh) when compared to the demand.", default=None
    )
    baseline_heat_load: float | None = Field(description="Baseline heat used (kWh).", default=None)
    baseline_dhw_load: float | None = Field(description="Baseline heat used for domestic hot water (kWh).",
                                            default=None)
    baseline_ch_load: float | None = Field(description="Baseline heat used for central heating (kWh).", default=None)

    baseline_heat_shortfall: float | None = Field(
        description="Baseline heat shortfall (kWh) when compared to the demand.", default=None
    )
    baseline_ch_shortfall: float | None = Field(
        description="Baseline central heating (CH) shortfall (kWh) when compared to the demand.", default=None
    )
    baseline_dhw_shortfall: float | None = Field(
        description="Baseline domestic hot water (DHW) shortfall (kWh) when compared to the demand.", default=None
    )
    baseline_peak_hload_shortfall: float | None = Field(
        description="Baseline shortfall in meeting the peak heating demand calculated by an external source (such as PHPP)",
        default=None,
    )
    baseline_gas_import_cost: float | None = Field(description="Total spend (£) importing gas.", default=None)
    baseline_electricity_import_cost: float | None = Field(
        description="Baseline spend (£) importing electricity from the grid.", default=None
    )
    baseline_electricity_export_gain: float | None = Field(
        description="Baseline income (£) exporting electricity to this grid.", default=None
    )
    baseline_meter_cost: float | None = Field(
        description="Baseline cost of importing fuel/electricity minus revenue from exporting.", default=None
    )
    baseline_operating_cost: float | None = Field(
        description="Baseline meter cost minus operating costs for components.", default=None
    )
    baseline_net_present_value: float | None = Field(
        description="Baseline Net Present Value after repeating the simulation for the configured number of years.",
        default=None,
    )
    baseline_scope_1_emissions: float | None = Field(description="Baseline Scope 1 emissions (kg CO2e).", default=None)
    baseline_scope_2_emissions: float | None = Field(description="Baseline Scope 2 emissions (kg CO2e).", default=None)
    baseline_combined_carbon_emissions: float | None = Field(
        description="Baseline Scope 1 and Scope 2 emissions (kg CO2e).", default=None
    )
    baseline_environmental_impact_score: int | None = Field(
        description="baseline environmental impact score based on SAP", default=None
    )
    baseline_environmental_impact_grade: Grade | None = Field(
        description="baseline environmental impact grade (A-G)", default=None
    )


class ReportData(BaseModel):
    """The output timeseries computed by an EPOCH simulation."""

    # TempSum
    Actual_import_shortfall: list[float] | None = Field(default=None, description="Time series of electrical import shortfall in kWh.")
    Actual_curtailed_export: list[float] | None = Field(default=None, description="Time series of curtailed exports in kWh.")
    Heat_shortfall: list[float] | None = Field(default=None, description="Time series of the total heat shortfall in kWh.")
    DHW_Shortfall: list[float] | None = Field(default=None, description="Time series of the domestic hot water (DHW) shortfall in kWh.")
    CH_shortfall: list[float] | None = Field(default=None, description="Time series of the central heating (CH) shortfall in kWh.")

    Heat_surplus: list[float] | None = Field(default=None, description="Time series of heat surplus in kWh.")

    # Hotel
    Hotel_load: list[float] | None = Field(default=None, description="Time series of the baseline electrical load in kWh.")
    Heatload: list[float] | None = Field(default=None, description="Time series of the heat demand in kWh; reduced by insulation.")
    CH_demand: list[float] | None = Field(default=None, description="Time series of Central Heating demand in kWh.")
    DHW_demand: list[float] | None = Field(default=None, description="Time series of Domestic Hot Water demand in kWh.")

    # PV
    PVdcGen: list[float] | None = Field(default=None, description="Time series of DC solar generation in kWh.")
    PVacGen: list[float] | None = Field(default=None, description="Time series of AC solar generation in kWh.")

    # EV
    EV_targetload: list[float] | None = Field(default=None, description="Time series for the target electrical vehicle load in kWh.")
    EV_actualload: list[float] | None = Field(default=None, description="Time series for the actual electrical vehicle load in kWh.")

    # ESS
    ESS_charge: list[float] | None = Field(default=None, description="Time series of battery charging during each timestep in kWh.")
    ESS_discharge: list[float] | None = Field(default=None, description="Time series of battery discharging during each timestep in kWh.")
    ESS_resulting_SoC: list[float] | None = Field(default=None, description="Time series of the state of charge of the battery in kWh")
    ESS_AuxLoad: list[float] | None = Field(default=None, description="Time series of the auxiliary battery load in kWh.")
    ESS_RTL: list[float] | None = Field(default=None, description="Time series of the battery round trip loss in kWh.")

    # DataCentre
    Data_centre_target_load: list[float] | None = Field(default=None, description="Time series of the data centre target load in kWh.")
    Data_centre_actual_load: list[float] | None = Field(default=None, description="Time series of the data centre actual load in kWh.")
    Data_centre_target_heat: list[float] | None = Field(default=None, description="Time series of the data centre target heat in kWh.")
    Data_centre_available_hot_heat: list[float] | None = Field(default=None, description="Time series of the available heat from the data centre in kWh.")

    # Grid
    Grid_Import: list[float] | None = Field(default=None, description="Time series of the electricity imported from the grid in kWh.")
    Grid_Export: list[float] | None = Field(default=None, description="Time series of the electricity exported to the grid in kWh.")

    # MOP
    MOP_load: list[float] | None = Field(default=None, description="Time series of the heat consumed by the mop load in kWh.")

    # GasCombustionHeater
    GasCH_load: list[float] | None = Field(default=None, description="Time series of the gas consumed by the boiler in kWh.")

    # DHW
    DHW_load: list[float] | None = Field(default=None, description="Time series of the heat drawn from the Hot Water Cylinder in kWh.")
    DHW_charging: list[float] | None = Field(default=None, description="Time series of the heat added to the Hot Water Cylinder during this timestep in kWh")
    DHW_SoC: list[float] | None = Field(default=None, description="Time series of the state of charge of the Hot Water Cylinder in kWh.")
    DHW_Standby_loss: list[float] | None = Field(default=None, description="Time series of the heat wasted to standby loss in the Hot Water Cylinder at each timestep in kWh.")
    DHW_ave_temperature: list[float] | None = Field(default=None, description="Time series of average temperature of the Hot Water Cylinder in degrees Celsius.")
    DHW_immersion_top_up: list[float] | None = Field(default=None, description="Time series of the DHW demand that the Hot Water Cylinder was unable to meet; requiring an immersion heater.")
    DHW_diverter_load: list[float] | None = Field(default=None, description="Time series of any renewable surplus that is diverted to resistive DHW heating.")
    DHW_resistive_load: list[float] | None = Field(default=None, description="Time series of the portion of the DHW demand that has been converted to electrical load in kWh.")

    # ASHP
    ASHP_elec_load: list[float] | None = Field(default=None, description="Time series of the heat pump's electrical load in kWh.")
    ASHP_DHW_output: list[float] | None = Field(default=None, description="Time series of the heat pump's heat output for hot water in kWh.")
    ASHP_CH_output: list[float] | None = Field(default=None, description="Time series of the heat pump's heat output for central heating in kWh.")
    ASHP_free_heat: list[float] | None = Field(default=None, description="Time series of the free heat drawn from ambient air for the heat pump in kWh.")
    ASHP_used_hotroom_heat: list[float] | None = Field(default=None, description="Time series of the heat drawn from the data centre hot room for the heat pump in kWh.")


class CostInfo(BaseModel):
    name: str = Field(examples=["Solar Panel"], description="Display name for this cost item.")
    component: str | None = Field(
        examples=["solar_panel"], description="Key of the EPOCH component type this cost belongs to.", default=None
    )
    cost: float = Field(
        examples=[1200.0], description="The net cost of the item in pounds, including all sub_components minus any funding."
    )
    sub_components: list[CostInfo] = Field(
        description="The sub-components that make up this cost item, or the empty list if there are none.", default_factory=list
    )
