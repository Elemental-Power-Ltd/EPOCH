
from pydantic import BaseModel, Field


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
    DHW_resistive_load: list[float] | None = Field(default=None, description="Time series of the portion of the DHW demand that has been converted to electrical load in kWh.")

    # ASHP
    ASHP_elec_load: list[float] | None = Field(default=None, description="Time series of the heat pump's electrical load in kWh.")
    ASHP_DHW_output: list[float] | None = Field(default=None, description="Time series of the heat pump's heat output for hot water in kWh.")
    ASHP_CH_output: list[float] | None = Field(default=None, description="Time series of the heat pump's heat output for central heating in kWh.")
    ASHP_free_heat: list[float] | None = Field(default=None, description="Time series of the free heat drawn from ambient air for the heat pump in kWh.")
    ASHP_used_hotroom_heat: list[float] | None = Field(default=None, description="Time series of the heat drawn from the data centre hot room for the heat pump in kWh.")
