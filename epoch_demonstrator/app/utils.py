from __future__ import annotations

from typing import TYPE_CHECKING

from app.models import CostInfo, Grade, ReportData, SimulationMetrics
from epoch_simulator import ReportData as EpochReportData

if TYPE_CHECKING:
    from epoch_simulator import ReportData, SimulationResult


def convert_capex_breakdown_to_pydantic(capex_breakdown: dict[str, any]) -> list[CostInfo]:
    """
    Convert an Epoch CapexBreakdown into a pydantic list of CostInfo objects.

    Parameters
    ----------
    capex_breakdown
        The CapexBreakdown instance to convert.

    Returns
    -------
        A list of pydantic CostInfo models.
    """
    costs = []

    if capex_breakdown.building_fabric_capex > 0:
        sub_comps = [CostInfo(name=f.name, cost=f.cost) for f in capex_breakdown.fabric_cost_breakdown]

        costs.append(
            CostInfo(
                name="Building Fabric",
                component="building",
                cost=capex_breakdown.building_fabric_capex,
                sub_components=sub_comps,
            )
        )

    if capex_breakdown.dhw_capex > 0:
        costs.append(CostInfo(name="Hot Water Cylinder", component="hot_water_cylinder", cost=capex_breakdown.dhw_capex))

    total_ev_capex = capex_breakdown.ev_charger_cost + capex_breakdown.ev_charger_install
    if total_ev_capex > 0:
        charger_cost = CostInfo(name="EV Charger Unit", cost=capex_breakdown.ev_charger_cost)
        install_cost = CostInfo(name="EV Charger Installation", cost=capex_breakdown.ev_charger_install)

        costs.append(
            CostInfo(
                name="Electric Vehicle Chargers",
                component="electric_vehicles",
                cost=total_ev_capex,
                sub_components=[charger_cost, install_cost],
            )
        )

    if capex_breakdown.gas_heater_capex > 0:
        costs.append(CostInfo(name="Gas Heater", component="gas_heater", cost=capex_breakdown.gas_heater_capex))

    if capex_breakdown.grid_capex > 0:
        costs.append(CostInfo(name="Grid Upgrade", component="grid", cost=capex_breakdown.grid_capex))

    if capex_breakdown.heatpump_capex > 0:
        costs.append(CostInfo(name="Heat Pump", component="heat_pump", cost=capex_breakdown.heatpump_capex))

    ess_capex = capex_breakdown.ess_pcs_capex + capex_breakdown.ess_enclosure_capex + capex_breakdown.ess_enclosure_disposal
    if ess_capex > 0:
        pcs_cost = CostInfo(name="ESS Power Conversion System", cost=capex_breakdown.ess_pcs_capex)
        enclosure_cost = CostInfo(name="ESS Enclosure", cost=capex_breakdown.ess_enclosure_capex)
        enclosure_disposal = CostInfo(name="ESS Enclosure Disposal", cost=capex_breakdown.ess_enclosure_disposal)

        costs.append(
            CostInfo(
                name="Energy Storage System",
                component="energy_storage_system",
                cost=ess_capex,
                sub_components=[pcs_cost, enclosure_cost, enclosure_disposal],
            )
        )

    total_pv_capex = (
        capex_breakdown.pv_panel_capex
        + capex_breakdown.pv_roof_capex
        + capex_breakdown.pv_ground_capex
        + capex_breakdown.pv_BoP_capex
    )
    if total_pv_capex > 0:
        panel_capex = CostInfo(name="Panel", cost=capex_breakdown.pv_panel_capex)
        # for simplicity, combine ground_capex and roof_capex into a single installation line item
        install_capex = CostInfo(
            name="Panel Installation", cost=capex_breakdown.pv_ground_capex + capex_breakdown.pv_roof_capex
        )
        balance_of_plant = CostInfo(name="Balance of Plant", cost=capex_breakdown.pv_BoP_capex)

        costs.append(
            CostInfo(
                name="Solar Panels",
                component="solar_panels",
                cost=total_pv_capex,
                sub_components=[panel_capex, install_capex, balance_of_plant],
            )
        )

    # for funding, EPOCH returns positive values, which it subtracts from the total capex
    # it makes more sense to display them as negative amounts in the GUI so we'll flip them

    # BUS could be a sub_component of the Heat Pump but for now we'll all funding at the end for simplicity
    if capex_breakdown.boiler_upgrade_scheme_funding != 0:
        costs.append(CostInfo(name="Boiler Upgrade Scheme", cost=-1 * capex_breakdown.boiler_upgrade_scheme_funding))

    if capex_breakdown.general_grant_funding != 0:
        costs.append(CostInfo(name="General Grant Funding", cost=-1 * capex_breakdown.general_grant_funding))

    return costs


def simulation_result_to_pydantic(sim_result: SimulationResult) -> SimulationMetrics:
    """
    Convert and EPOCH SimulationResult into a Pydantic SiteMetrics object.

    Parameters
    ----------
    sim_result
        Epoch bindings for a SimulationResult.

    Returns
    -------
    SimulationMetrics
        A pydantic model of the metrics.
    """
    comp = sim_result.comparison
    scenario = sim_result.metrics
    baseline = sim_result.baseline_metrics

    # we have to do an awkward conversion between two enums with the same values here
    scenario_grade = (
        Grade[scenario.environmental_impact_grade.name] if scenario.environmental_impact_grade is not None else None
    )
    baseline_grade = (
        Grade[baseline.environmental_impact_grade.name] if baseline.environmental_impact_grade is not None else None
    )

    return SimulationMetrics(
        # Comparison metrics
        meter_balance=comp.meter_balance,
        operating_balance=comp.operating_balance,
        cost_balance=comp.cost_balance,
        npv_balance=comp.npv_balance,
        payback_horizon=comp.payback_horizon_years,
        return_on_investment=comp.return_on_investment,
        carbon_balance_scope_1=comp.carbon_balance_scope_1,
        carbon_balance_scope_2=comp.carbon_balance_scope_2,
        carbon_balance_total=comp.combined_carbon_balance,
        carbon_cost=comp.carbon_cost,
        # Scenario Metrics
        total_gas_used=scenario.total_gas_used,
        total_electricity_imported=scenario.total_electricity_imported,
        total_electricity_generated=scenario.total_electricity_generated,
        total_electricity_exported=scenario.total_electricity_exported,
        total_electricity_curtailed=scenario.total_electricity_curtailed,
        total_electricity_used=scenario.total_electricity_used,
        total_electrical_shortfall=scenario.total_electrical_shortfall,
        total_heat_load=scenario.total_heat_load,
        total_dhw_load=scenario.total_dhw_load,
        total_ch_load=scenario.total_ch_load,
        total_heat_shortfall=scenario.total_heat_shortfall,
        total_ch_shortfall=scenario.total_ch_shortfall,
        total_dhw_shortfall=scenario.total_dhw_shortfall,
        peak_hload_shortfall=scenario.peak_hload_shortfall,
        capex=scenario.total_capex,
        total_gas_import_cost=scenario.total_gas_import_cost,
        total_electricity_import_cost=scenario.total_electricity_import_cost,
        total_electricity_export_gain=scenario.total_electricity_export_gain,
        total_meter_cost=scenario.total_meter_cost,
        total_operating_cost=scenario.total_operating_cost,
        annualised_cost=scenario.total_annualised_cost,
        total_net_present_value=scenario.total_net_present_value,
        total_scope_1_emissions=scenario.total_scope_1_emissions,
        total_scope_2_emissions=scenario.total_scope_2_emissions,
        total_combined_carbon_emissions=scenario.total_combined_carbon_emissions,
        scenario_environmental_impact_score=scenario.environmental_impact_score,
        scenario_environmental_impact_grade=scenario_grade,
        scenario_capex_breakdown=convert_capex_breakdown_to_pydantic(sim_result.scenario_capex_breakdown),
        # Baseline Metrics
        baseline_gas_used=baseline.total_gas_used,
        baseline_electricity_imported=baseline.total_electricity_imported,
        baseline_electricity_generated=baseline.total_electricity_generated,
        baseline_electricity_exported=baseline.total_electricity_exported,
        baseline_electricity_curtailed=baseline.total_electricity_curtailed,
        baseline_electricity_used=baseline.total_electricity_used,
        baseline_electrical_shortfall=baseline.total_electrical_shortfall,
        baseline_heat_load=baseline.total_heat_load,
        baseline_dhw_load=baseline.total_dhw_load,
        baseline_ch_load=baseline.total_ch_load,
        baseline_heat_shortfall=baseline.total_heat_shortfall,
        baseline_ch_shortfall=baseline.total_ch_shortfall,
        baseline_dhw_shortfall=baseline.total_dhw_shortfall,
        baseline_peak_hload_shortfall=baseline.peak_hload_shortfall,
        baseline_gas_import_cost=baseline.total_gas_import_cost,
        baseline_electricity_import_cost=baseline.total_electricity_import_cost,
        baseline_electricity_export_gain=baseline.total_electricity_export_gain,
        baseline_meter_cost=baseline.total_meter_cost,
        baseline_operating_cost=baseline.total_operating_cost,
        baseline_net_present_value=baseline.total_net_present_value,
        baseline_scope_1_emissions=baseline.total_scope_1_emissions,
        baseline_scope_2_emissions=baseline.total_scope_2_emissions,
        baseline_combined_carbon_emissions=baseline.total_combined_carbon_emissions,
        baseline_environmental_impact_score=baseline.environmental_impact_score,
        baseline_environmental_impact_grade=baseline_grade,
    )


def report_data_to_dict(report_data: any) -> dict[str, list[float]]:
    """
    Convert the ReportData type returned as part of a SimulationResult into a more generic dict type.

    This is a convenience method to make the type we provide to the GUI generic (for now).

    Parameters
    ----------
    report_data
        The python bindings for the EPOCH ReportData struct

    Returns
    -------
        A dictionary representation of the report_data
    """

    def filter_report_data_fields(fields: list[str]) -> list[str]:
        """
        Crude method of finding the useful report data's fields.

        Filter out the methods that start with "__" and "_pybind11_conduit_v1_".

        Parameters
        ----------
        fields
            list of fields to filter.

        Returns
        -------
            list of filtered fields.
        """
        return [field for field in fields if field != "_pybind11_conduit_v1_" and not field.startswith("__")]

    report_dict = {}
    if report_data is not None:
        fields = filter_report_data_fields(fields=dir(report_data))

        # all fields are currently numpy arrays
        # we want the non-zero arrays
        for field in fields:
            vector = getattr(report_data, field)
            if vector.any():
                report_dict[field] = vector.tolist()
    return report_dict


def report_data_to_pydantic(report_data: ReportData | EpochReportData) -> ReportData:
    """
    Convert the C++ / Pybind report_data type into a pydantic model (via a json dict).

    Parameters
    ----------
    report_data
        pybind / C++ output report data

    Returns
    -------
    ReportData
        pydantic type
    """
    return ReportData.model_validate(report_data_to_dict(report_data))
