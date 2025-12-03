"""
Endpoints to store the requests and results of optimisation tasks.

Each optimisation task should start by filing the job config in the database,
and then later on add the results.
Each result is uniquely identified, and belongs to a set of results.
"""

import asyncio
import functools
import json
import logging
from collections import defaultdict
from typing import cast

import asyncpg
import numpy as np
from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder

from app.dependencies import DatabasePoolDep
from app.internal.epl_typing import Jsonable
from app.internal.optimisation import pick_highlighted_results
from app.internal.optimisation.highlight import get_curated_results
from app.internal.optimisation.util import capex_breakdown_from_json, capex_breakdown_to_json
from app.internal.utils.utils import ArgDefaultDict, snake_to_title_case
from app.internal.utils.uuid import uuid7
from app.models.core import ResultID, TaskID, dataset_id_t, site_id_t
from app.models.optimisation import (
    AddCuratedResultRequest,
    CuratedResult,
    FixedParam,
    Grade,
    LegacyResultReproConfig,
    ListCuratedResultsResponse,
    MinMaxParam,
    NewResultReproConfig,
    OptimisationResultEntry,
    OptimisationResultsResponse,
    OptimisationTaskListEntry,
    OptimisationTaskListRequest,
    OptimisationTaskListResponse,
    Param,
    PortfolioOptimisationResult,
    SearchInfo,
    SimulationMetrics,
    SiteOptimisationResult,
    TaskConfig,
    ValuesParam,
    component_t,
    gui_param_dict,
    result_repro_config_t,
)
from app.models.site_manager import BundleHints, SiteDataEntry
from app.models.site_range import SiteRange
from app.routers.site_manager import get_bundle_hints

router = APIRouter()

type site_search_space_dict = dict[component_t, gui_param_dict | list[gui_param_dict]]


def values_to_param(
    values: list[float] | list[int] | list[str], can_minmax: bool = True
) -> ValuesParam | MinMaxParam[float] | MinMaxParam[int] | FixedParam:
    """
    Convert a list of values into the most GUI friendly form.

    If we've only got one value, or the min and max are the same, then return just that fixed value.
    If we've got a few values, or they're strings, then return a list of those values.
    If we've got a lot of values, condense them into a `min`, `max` pair.
    Some parameters, like tariff indices, mustn't be condensed itno a `MinMaxParam` and will always be
    either a `FixedParam` or `ValuesParam`.

    Parameters
    ----------
    values
        List of searched values
    can_minmax
        Whether it's valid to turn this parameter into a minmax parameter or if it must be kept as a list.

    Returns
    -------
    ValuesParam
        A list of values if they're strings or if this is a short collection
    FixedParam
        A single value
    MinMaxParam
        If the range is large or we searched many.
    """
    if min(values) == max(values) or len(values) == 1:
        return snake_to_title_case(values[0]) if isinstance(values[0], str) else values[0]

    # Leave this one be! It's probably a tariff index or fabric intervention index..
    if not can_minmax:
        return values

    # In the case of short lists, just return them all
    if len(values) <= 4:
        return values

    # if we've got a string enum, then don't turn it into a MinMaxParam.
    if any(isinstance(v, str) for v in values):
        return cast(ValuesParam, [snake_to_title_case(x) if isinstance(x, str) else x for x in values])

    return MinMaxParam(min=cast(float | int, min(values)), max=cast(float | int, max(values)), count=len(values))


def db_to_gui_site_range(db_site_range: SiteRange) -> dict[component_t, gui_param_dict | list[gui_param_dict]]:
    """
    Convert a single site range from the database into a GUI friendly version.

    This will split the dictionary into one keyed by components with the values being either
    a single gui-friendly dict, or a list of gui-friendly dicts (in the case of solar panels).
    It works as defensively as possible, and should cope with all types of site range.
    This skips incumbent assets as we assume that they're already there (and are therefore not interventions).

    Parameters
    ----------
    db_site_range
        A site range from the database which might be old.

    Returns
    -------
    dict[component_t, gui_param_t | list[gui_param_t]]
        Component types are like `heat_pump` or `solar_panels`
        A gui_param_t is then like `{"heat_power": Param(...)}` for each parameter

    """
    logger = logging.getLogger(__name__)

    # These are manually maintained, but should be broadly sensible.
    # If we have a parameter name clash between components then they should have the same units.
    param_names = ArgDefaultDict[str, str](default_factory=lambda x: snake_to_title_case(x))
    param_names |= {
        "send_temp": "Send Temperature",
        "fabric_intervention_index": "Fabric Intervention",
        "tariff_index": "Import Tariff",
    }

    discrete_params = frozenset(["tariff_index", "fabric_intervention_index", "yield_index"])

    param_units = defaultdict(lambda: None) | {
        # Building
        "floor_area": "m²",
        # Battery
        "capacity": "kWh",
        "charge_power": "kW",
        "discharge_power": "kW",
        "initial_charge": "%",
        # DHW cylinder
        "cylinder_volume": "L",
        # Electric Vehicles
        "flexible_load_ratio": "%",
        # Gas heater
        "maximum_output": "kW",
        "boiler_efficiency": "%",
        "fixed_gas_price": "£/kWh",
        # Data Centre
        "maximum_load": "kW",
        "hotroom_temperature": "°C",
        # Grid Connection
        "grid_export": "kW",
        "grid_import": "kW",
        "import_headroom": "%",
        "export_headroom": "%",
        "export_tariff": "£/kWh",
        # Heat Pump
        "heat_power": "kWth",
        "send_temp": "°C",
        # Solar
        "yield_scalar": "kWp",
    }
    params_to_skip = frozenset({
        "age",
        "lifetime",
        "COMPONENT_IS_MANDATORY",
        "scalar_heat_load",
        "scalar_electrical_load",
        "min_power_factor",
        "incumbent",
        "floor_area",
    })

    def value_to_param_dict(value: dict[str, Jsonable]) -> gui_param_dict | None:
        """
        Split a single value into a parameter dictionary.

        The value is what we store for this component in the search space, and will be a dictionary
        of parameters and a list of searched values.
        Turn this into a pydantic param dict with some prettifying and sort out the values list as well.

        Parameters
        ----------
        value
            A database-style search space for a single component e.g. {"heat_power": [100, 200, 300]}

        Returns
        -------
        gui_param_dict
            A parsed GUI friendly parameter dict if we can
        None
            if this component is incumbent or something went wrong.
        """
        # Note that we return the search space for incumbent components as well,
        # as they might not be fully incumbent! (e.g. changing tariffs)
        new_dict: gui_param_dict = {}
        for param, param_values in value.items():
            if param in params_to_skip or not isinstance(param_values, list):
                continue
            new_dict[param] = Param(
                name=param_names[param],
                units=param_units[param],
                considered=values_to_param(cast(list, param_values), can_minmax=param not in discrete_params),
            )
        return new_dict

    gui_site_range: dict[component_t, gui_param_dict | list[gui_param_dict]] = {}

    for component, value in db_site_range.items():
        if value is None:
            continue
        if component == "config":
            # Don't parse the config for now as it contains ugly NSGA2 hyperparameters etc.
            # We might want to do this in future?
            continue
        # We do these two-step assignments to filter out the cases where we didn't get valid
        # dicts
        if isinstance(value, list):
            # We know these are dict[str, Jsonable] so we're fine
            parsed_list = [value_to_param_dict(cast(dict, subvalue)) for subvalue in value]
            gui_site_range[component] = [item for item in parsed_list if item]
        elif isinstance(value, dict):
            if parsed := value_to_param_dict(value):
                gui_site_range[component] = parsed
        else:
            logger.warning(f"Got unprocessable site range component: {component}: {value}")

    return gui_site_range


async def get_gui_site_range(task_id: TaskID, pool: DatabasePoolDep) -> dict[site_id_t, site_search_space_dict]:
    """
    Get a site range suitable for the GUI associated with this task ID.

    This will be sorted by site and have a friendly way of displaying the parameters.
    Not all parameters will be included, and some will be single values.

    Parameters
    ----------
    task_id
        ID of the task to get the GUI site range for

    pool
        Database connection pool to look up with.

    Returns
    -------
    dict[site_id_t, gui_param_t]
        Dictionary keyed by site names, with each sub-dictionary being a param name followed by a dictionary of parameters
        you might want to display
        e.g. {"demo_london":
                {"heat_pump":
                    {"heat_power": Param(name="Heat Power", units="kWth", considered=MinMaxParam[float](min=4.0, max=12.0))}
                }
            }
    """
    rows = await pool.fetch(
        """
        SELECT
            site_id,
            site_range
        FROM
            optimisation.site_task_config
        WHERE task_id = $1
        """,
        task_id.task_id,
    )
    ranges = {}
    for site_id, site_range in rows:
        ranges[str(site_id)] = db_to_gui_site_range(json.loads(site_range))
    return ranges


def patch_hints_into_site_range(site_range: site_search_space_dict, hints: BundleHints) -> site_search_space_dict:
    """
    Replace the indices that we sometimes get with human-readable hinted names.

    This is reasonably general, but if we don't find a hint then we'll leave you with the indices.

    Parameters
    ----------
    site_range
        A GUI friendly site range, potentially with indices for tariffs, fabric intervention etc

    hints
        A GUI friendly set of bundle hints including names

    Returns
    -------
    site_search_space_dict
        A search space dictionary like `site_range` but with human readable names instead of indices.
    """
    logger = logging.getLogger(__name__)
    if "grid" in site_range and "tariff_index" in site_range["grid"] and hints.tariffs:
        try:
            range_to_hint = cast(dict, site_range["grid"])["tariff_index"].considered
            tariff_hints = hints.tariffs
            # We know that tariff indexes are either a list[int] or int, and never a minmaxparam.
            if isinstance(range_to_hint, int):
                cast(dict, site_range["grid"])["tariff_index"].considered = snake_to_title_case(
                    tariff_hints[range_to_hint].product_name
                )
            elif isinstance(range_to_hint, list):
                for i, idx in enumerate(range_to_hint):
                    range_to_hint[i] = snake_to_title_case(tariff_hints[idx].product_name)
            else:
                logger.warning(f"Got a bad type for {site_range['grid']['tariff_index']}, can't patch hints")  # type: ignore
        except Exception as ex:
            logger.exception(f"Got a {type(ex).__name__} while patching grid hints")
            pass

    if "building" in site_range and "fabric_intervention_index" in site_range["building"] and hints.heating:
        try:
            heating_hints = hints.heating
            # We know that fabric intervention indexes are either a list[int] or int, and never a minmaxparam.
            range_to_hint = site_range["building"]["fabric_intervention_index"].considered  # type: ignore
            if isinstance(range_to_hint, int):
                cast(dict, site_range["building"])["fabric_intervention_index"].considered = ", ".join(
                    snake_to_title_case(item) for item in heating_hints[range_to_hint].interventions
                )
            elif isinstance(range_to_hint, list):
                for i, idx in enumerate(range_to_hint):
                    # note: we allow for the empty list to represent no interventions
                    range_to_hint[i] = ", ".join(snake_to_title_case(item) for item in heating_hints[idx].interventions)
            else:
                logger.warning(
                    f"Got a bad type for {site_range['building']['fabric_intervention_index'].considered}, can't patch hints"  # type: ignore
                )
        except Exception as ex:
            logger.exception(f"Got a {type(ex).__name__} while patching grid hints")
            pass

    if "solar_panels" in site_range and hints.renewables:
        # Rename the "name" parameter of this variable to the solar location, or combination of solar locations.
        renewables_hints = hints.renewables
        try:
            for i, param in enumerate(site_range["solar_panels"]):
                yield_indices = param["yield_index"].considered  # type: ignore
                if isinstance(yield_indices, int):
                    yield_indices = [yield_indices]
                # It's possible to choose between locations when searching.
                # In that case, join them all together with commas in between.
                # We use 'Default' in instances where the name is None
                yield_index_name = ", ".join((renewables_hints[j].name or "Default") for j in yield_indices)
                cast(list, site_range["solar_panels"])[i]["yield_scalar"].name = yield_index_name

                # Remove this entry as it's confusing once hinted
                del site_range["solar_panels"][i]["yield_index"]  # type: ignore
        except Exception as ex:
            logger.exception(f"Got a {type(ex).__name__} while patching grid hints")
            pass
    return site_range


def get_search_info(gui_search_range: dict[site_id_t, site_search_space_dict]) -> SearchInfo:
    """
    Get supporting information about the optimisation job we have run.

    Parameters
    ----------
    gui_search_range
        the version of the SiteRange designed for GUI consumption.

    Returns
    -------
    A SearchInfo model containing total search space counts.
    """

    def count_total_params(site_range: dict[component_t, gui_param_dict | list[gui_param_dict]]) -> int:
        """
        Count the total size of the search space that we've considered.

        This recurses into each component and splits out the lists, minmax params to get the total count.
        This may be extremely large!

        Parameters
        ----------
        site_range
            Populated site range in the GUI form (do this at the end of the function)

        Returns
        -------
        int
            Number of entries in the search space.
        """
        total_params = 1
        for param in site_range.values():
            if isinstance(param, list):
                for subparam in param:
                    for subparam_val in subparam.values():
                        if isinstance(subparam_val.considered, list):
                            total_params *= len(subparam_val.considered)
                        elif isinstance(subparam_val.considered, MinMaxParam):
                            total_params *= subparam_val.considered.count
            else:
                for subparam_val in param.values():
                    if isinstance(subparam_val.considered, list):
                        total_params *= len(subparam_val.considered)
                    elif isinstance(subparam_val.considered, MinMaxParam):
                        total_params *= subparam_val.considered.count
        return total_params

    portfolio_total = 1
    search_sizes: dict[site_id_t, int] = {}
    for site in gui_search_range:
        site_total = count_total_params(gui_search_range[site])
        search_sizes[site] = site_total
        portfolio_total *= site_total

    return SearchInfo(total_options_considered=portfolio_total, site_options_considered=search_sizes)


@router.post("/get-optimisation-results")
async def get_optimisation_results(task_id: TaskID, pool: DatabasePoolDep) -> OptimisationResultsResponse:
    """
    Get all the optimisation results for a single task.

    This looks up for a specific task ID, which you filed in `/add-optimisation-job`.
    The set of task IDs for a given client can also be queried with /list-optimisation-tasks

    Parameters
    ----------
    task_id
        ID of a specific optimisation task that was run

    Returns
    -------
    results
        List of optimisation results, including the EPOCH parameters under 'solutions'
    """
    res = await pool.fetch(
        """
        SELECT
            pr.task_id,
            pr.portfolio_id,
            ANY_VALUE(pr.is_feasible) AS is_feasible,
            ANY_VALUE(pr.metric_meter_balance) AS metric_meter_balance,
            ANY_VALUE(pr.metric_operating_balance) AS metric_operating_balance,
            ANY_VALUE(pr.metric_cost_balance) AS metric_cost_balance,
            ANY_VALUE(pr.metric_npv_balance) as metric_npv_balance,
            ANY_VALUE(pr.metric_payback_horizon) AS metric_payback_horizon,
            ANY_VALUE(pr.metric_return_on_investment) AS metric_return_on_investment,
            ANY_VALUE(pr.metric_carbon_balance_scope_1) AS metric_carbon_balance_scope_1,
            ANY_VALUE(pr.metric_carbon_balance_scope_2) AS metric_carbon_balance_scope_2,
            ANY_VALUE(pr.metric_combined_carbon_balance) AS metric_combined_carbon_balance,
            ANY_VALUE(pr.metric_carbon_cost) AS metric_carbon_cost,

            ANY_VALUE(pr.metric_total_gas_used) AS metric_total_gas_used,
            ANY_VALUE(pr.metric_total_electricity_imported) AS metric_total_electricity_imported,
            ANY_VALUE(pr.metric_total_electricity_generated) AS metric_total_electricity_generated,
            ANY_VALUE(pr.metric_total_electricity_exported) AS metric_total_electricity_exported,
            ANY_VALUE(pr.metric_total_electricity_curtailed) AS metric_total_electricity_curtailed,
            ANY_VALUE(pr.metric_total_electricity_used) AS metric_total_electricity_used,
            ANY_VALUE(pr.metric_total_electrical_shortfall) AS metric_total_electrical_shortfall,
            ANY_VALUE(pr.metric_total_heat_load) AS metric_total_heat_load,
            ANY_VALUE(pr.metric_total_dhw_load) AS metric_total_dhw_load,
            ANY_VALUE(pr.metric_total_ch_load) AS metric_total_ch_load,
            ANY_VALUE(pr.metric_total_heat_shortfall) AS metric_total_heat_shortfall,
            ANY_VALUE(pr.metric_total_ch_shortfall) AS metric_total_ch_shortfall,
            ANY_VALUE(pr.metric_total_dhw_shortfall) AS metric_total_dhw_shortfall,
            ANY_VALUE(pr.metric_peak_hload_shortfall) AS metric_peak_hload_shortfall,
            ANY_VALUE(pr.metric_capex) AS metric_capex,
            ANY_VALUE(pr.metric_total_gas_import_cost) AS metric_total_gas_import_cost,
            ANY_VALUE(pr.metric_total_electricity_import_cost) AS metric_total_electricity_import_cost,
            ANY_VALUE(pr.metric_total_electricity_export_gain) AS metric_total_electricity_export_gain,
            ANY_VALUE(pr.metric_total_meter_cost) AS metric_total_meter_cost,
            ANY_VALUE(pr.metric_total_operating_cost) AS metric_total_operating_cost,
            ANY_VALUE(pr.metric_annualised_cost) AS metric_annualised_cost,
            ANY_VALUE(pr.metric_total_net_present_value) AS metric_total_net_present_value,
            ANY_VALUE(pr.metric_total_scope_1_emissions) AS metric_total_scope_1_emissions,
            ANY_VALUE(pr.metric_total_scope_2_emissions) AS metric_total_scope_2_emissions,
            ANY_VALUE(pr.metric_total_combined_carbon_emissions) AS metric_total_combined_carbon_emissions,

            ANY_VALUE(pr.metric_baseline_gas_used) AS metric_baseline_gas_used,
            ANY_VALUE(pr.metric_baseline_electricity_imported) AS metric_baseline_electricity_imported,
            ANY_VALUE(pr.metric_baseline_electricity_generated) AS metric_baseline_electricity_generated,
            ANY_VALUE(pr.metric_baseline_electricity_exported) AS metric_baseline_electricity_exported,
            ANY_VALUE(pr.metric_baseline_electricity_curtailed) as metric_baseline_electricity_curtailed,
            ANY_VALUE(pr.metric_baseline_electricity_used) as metric_baseline_electricity_used,
            ANY_VALUE(pr.metric_baseline_electrical_shortfall) AS metric_baseline_electrical_shortfall,
            ANY_VALUE(pr.metric_baseline_heat_load) AS metric_baseline_heat_load,
            ANY_VALUE(pr.metric_baseline_dhw_load) AS metric_baseline_dhw_load,
            ANY_VALUE(pr.metric_baseline_ch_load) AS metric_baseline_ch_load,
            ANY_VALUE(pr.metric_baseline_heat_shortfall) AS metric_baseline_heat_shortfall,
            ANY_VALUE(pr.metric_baseline_ch_shortfall) as metric_baseline_ch_shortfall,
            ANY_VALUE(pr.metric_baseline_dhw_shortfall) as metric_baseline_dhw_shortfall,
            ANY_VALUE(pr.metric_baseline_peak_hload_shortfall) as metric_baseline_peak_hload_shortfall,
            ANY_VALUE(pr.metric_baseline_gas_import_cost) AS metric_baseline_gas_import_cost,
            ANY_VALUE(pr.metric_baseline_electricity_import_cost) AS metric_baseline_electricity_import_cost,
            ANY_VALUE(pr.metric_baseline_electricity_export_gain) AS metric_baseline_electricity_export_gain,
            ANY_VALUE(pr.metric_baseline_meter_cost) AS metric_baseline_meter_cost,
            ANY_VALUE(pr.metric_baseline_operating_cost) AS metric_baseline_operating_cost,
            ANY_VALUE(pr.metric_baseline_net_present_value) AS metric_baseline_net_present_value,
            ANY_VALUE(pr.metric_baseline_scope_1_emissions) AS metric_baseline_scope_1_emissions,
            ANY_VALUE(pr.metric_baseline_scope_2_emissions) AS metric_baseline_scope_2_emissions,
            ANY_VALUE(pr.metric_baseline_combined_carbon_emissions) as metric_baseline_combined_carbon_emissions,

            ARRAY_AGG(sr.*) AS site_results,
            ANY_VALUE(stc.site_bundle_ids) AS site_bundle_ids
        FROM
            optimisation.portfolio_results AS pr
        LEFT JOIN
            optimisation.site_results AS sr
        ON pr.portfolio_id = sr.portfolio_id
        LEFT JOIN
            (
                SELECT
                    task_id,
                    ARRAY_AGG(DISTINCT bundle_id) AS site_bundle_ids
                FROM optimisation.site_task_config
                GROUP BY task_id
            ) AS stc
        ON stc.task_id = pr.task_id
        WHERE pr.task_id = $1
        GROUP BY (pr.task_id, pr.portfolio_id)
        """,
        task_id.task_id,
    )

    # We got bundle IDs with each row in the task simulator, but they'll almost always be the same.
    # Get all the bundles that were used across the simulations (getting the total unique set,
    # just in case any sites were missed in row[0])
    # and get the hints for each one. Then, assign the hints per-bundle to the associated site.
    # This should work as each site has a single dataset bundle by design, and each site should only
    # have used one bundle in the entire simulation.
    # Be careful in future if sites use different bundles and use a different key for the tasks then.
    bundle_set = set()
    for item in res:
        if "site_bundle_ids" in item and item["site_bundle_ids"] is not None:
            bundle_set.update(item["site_bundle_ids"])
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(get_bundle_hints(bundle_id, pool)) for bundle_id in bundle_set if bundle_id is not None]

    bundle_hints = {item.result().site_id: item.result() for item in tasks}

    # Bind a local NaN to num with the defaults set reasonably, just in case
    # any have slipped through.
    nan_to_num = functools.partial(
        np.nan_to_num,
        nan=np.finfo(np.float32).max,  # be careful of this one!
        posinf=np.finfo(np.float32).max,
        neginf=np.finfo(np.float32).min,
    )  # pyright: ignore[reportCallIssue]
    portfolio_results = [
        PortfolioOptimisationResult(
            task_id=item["task_id"],
            portfolio_id=item["portfolio_id"],
            is_feasible=item["is_feasible"],
            metrics=SimulationMetrics(
                meter_balance=nan_to_num(item["metric_meter_balance"]),
                operating_balance=nan_to_num(item["metric_operating_balance"]),
                cost_balance=nan_to_num(item["metric_cost_balance"]),
                npv_balance=nan_to_num(item["metric_npv_balance"]),
                payback_horizon=nan_to_num(item["metric_payback_horizon"]),
                return_on_investment=nan_to_num(item["metric_return_on_investment"]),
                carbon_balance_scope_1=nan_to_num(item["metric_carbon_balance_scope_1"]),
                carbon_balance_scope_2=nan_to_num(item["metric_carbon_balance_scope_2"]),
                carbon_balance_total=nan_to_num(item["metric_combined_carbon_balance"]),
                carbon_cost=nan_to_num(item["metric_carbon_cost"]),
                # total metrics
                total_gas_used=nan_to_num(item["metric_total_gas_used"]),
                total_electricity_imported=nan_to_num(item["metric_total_electricity_imported"]),
                total_electricity_generated=nan_to_num(item["metric_total_electricity_generated"]),
                total_electricity_exported=nan_to_num(item["metric_total_electricity_exported"]),
                total_electricity_curtailed=nan_to_num(item["metric_total_electricity_curtailed"]),
                total_electricity_used=nan_to_num(item["metric_total_electricity_used"]),
                total_electrical_shortfall=nan_to_num(item["metric_total_electrical_shortfall"]),
                total_heat_load=nan_to_num(item["metric_total_heat_load"]),
                total_dhw_load=nan_to_num(item["metric_total_dhw_load"]),
                total_ch_load=nan_to_num(item["metric_total_ch_load"]),
                total_heat_shortfall=nan_to_num(item["metric_total_heat_shortfall"]),
                total_ch_shortfall=nan_to_num(item["metric_total_ch_shortfall"]),
                total_dhw_shortfall=nan_to_num(item["metric_total_dhw_shortfall"]),
                peak_hload_shortfall=nan_to_num(item["metric_peak_hload_shortfall"]),
                capex=nan_to_num(item["metric_capex"]),
                total_gas_import_cost=nan_to_num(item["metric_total_gas_import_cost"]),
                total_electricity_import_cost=nan_to_num(item["metric_total_electricity_import_cost"]),
                total_electricity_export_gain=nan_to_num(item["metric_total_electricity_export_gain"]),
                total_meter_cost=nan_to_num(item["metric_total_meter_cost"]),
                total_operating_cost=nan_to_num(item["metric_total_operating_cost"]),
                annualised_cost=nan_to_num(item["metric_annualised_cost"]),
                total_net_present_value=nan_to_num(item["metric_total_net_present_value"]),
                total_scope_1_emissions=nan_to_num(item["metric_total_scope_1_emissions"]),
                total_scope_2_emissions=nan_to_num(item["metric_total_scope_2_emissions"]),
                total_combined_carbon_emissions=nan_to_num(item["metric_total_combined_carbon_emissions"]),
                # quirk of Portfolio vs Site results,
                # these columns don't exist in the portfolio table
                scenario_environmental_impact_score=None,
                scenario_environmental_impact_grade=None,
                scenario_capex_breakdown=None,
                # baseline metrics
                baseline_gas_used=nan_to_num(item["metric_baseline_gas_used"]),
                baseline_electricity_imported=nan_to_num(item["metric_baseline_electricity_imported"]),
                baseline_electricity_generated=nan_to_num(item["metric_baseline_electricity_generated"]),
                baseline_electricity_exported=nan_to_num(item["metric_baseline_electricity_exported"]),
                baseline_electricity_curtailed=nan_to_num(item["metric_baseline_electricity_curtailed"]),
                baseline_electricity_used=nan_to_num(item["metric_baseline_electricity_used"]),
                baseline_electrical_shortfall=nan_to_num(item["metric_baseline_electrical_shortfall"]),
                baseline_heat_load=nan_to_num(item["metric_baseline_heat_load"]),
                baseline_dhw_load=nan_to_num(item["metric_baseline_dhw_load"]),
                baseline_ch_load=nan_to_num(item["metric_baseline_ch_load"]),
                baseline_heat_shortfall=nan_to_num(item["metric_baseline_heat_shortfall"]),
                baseline_ch_shortfall=nan_to_num(item["metric_baseline_ch_shortfall"]),
                baseline_dhw_shortfall=nan_to_num(item["metric_baseline_dhw_shortfall"]),
                baseline_peak_hload_shortfall=nan_to_num(item["metric_baseline_peak_hload_shortfall"]),
                baseline_gas_import_cost=nan_to_num(item["metric_baseline_gas_import_cost"]),
                baseline_electricity_import_cost=nan_to_num(item["metric_baseline_electricity_import_cost"]),
                baseline_electricity_export_gain=nan_to_num(item["metric_baseline_electricity_export_gain"]),
                baseline_meter_cost=nan_to_num(item["metric_baseline_meter_cost"]),
                baseline_operating_cost=nan_to_num(item["metric_baseline_operating_cost"]),
                baseline_net_present_value=nan_to_num(item["metric_baseline_net_present_value"]),
                baseline_scope_1_emissions=nan_to_num(item["metric_baseline_scope_1_emissions"]),
                baseline_scope_2_emissions=nan_to_num(item["metric_baseline_scope_2_emissions"]),
                baseline_combined_carbon_emissions=nan_to_num(item["metric_baseline_combined_carbon_emissions"]),
                # quirk of Portfolio vs Site results,
                # these columns don't exist in the portfolio table
                baseline_environmental_impact_score=None,
                baseline_environmental_impact_grade=None,
            ),
            site_results=[
                SiteOptimisationResult(
                    site_id=sub_item["site_id"],
                    portfolio_id=sub_item["portfolio_id"],
                    scenario=json.loads(sub_item["scenario"]),
                    is_feasible=sub_item["is_feasible"],
                    metrics=SimulationMetrics(
                        meter_balance=nan_to_num(sub_item["metric_meter_balance"]),
                        operating_balance=nan_to_num(sub_item["metric_operating_balance"]),
                        cost_balance=nan_to_num(sub_item["metric_cost_balance"]),
                        npv_balance=nan_to_num(sub_item["metric_npv_balance"]),
                        payback_horizon=nan_to_num(sub_item["metric_payback_horizon"]),
                        return_on_investment=nan_to_num(sub_item["metric_return_on_investment"]),
                        carbon_balance_scope_1=nan_to_num(sub_item["metric_carbon_balance_scope_1"]),
                        carbon_balance_scope_2=nan_to_num(sub_item["metric_carbon_balance_scope_2"]),
                        carbon_balance_total=nan_to_num(sub_item["metric_combined_carbon_balance"]),
                        carbon_cost=nan_to_num(sub_item["metric_carbon_cost"]),
                        # total metrics
                        total_gas_used=nan_to_num(sub_item["metric_total_gas_used"]),
                        total_electricity_imported=nan_to_num(sub_item["metric_total_electricity_imported"]),
                        total_electricity_generated=nan_to_num(sub_item["metric_total_electricity_generated"]),
                        total_electricity_exported=nan_to_num(sub_item["metric_total_electricity_exported"]),
                        total_electricity_curtailed=nan_to_num(sub_item["metric_total_electricity_curtailed"]),
                        total_electricity_used=nan_to_num(sub_item["metric_total_electricity_used"]),
                        total_electrical_shortfall=nan_to_num(sub_item["metric_total_electrical_shortfall"]),
                        total_heat_load=nan_to_num(sub_item["metric_total_heat_load"]),
                        total_dhw_load=nan_to_num(sub_item["metric_total_dhw_load"]),
                        total_ch_load=nan_to_num(sub_item["metric_total_ch_load"]),
                        total_heat_shortfall=nan_to_num(sub_item["metric_total_heat_shortfall"]),
                        total_ch_shortfall=nan_to_num(sub_item["metric_total_ch_shortfall"]),
                        total_dhw_shortfall=nan_to_num(sub_item["metric_total_dhw_shortfall"]),
                        peak_hload_shortfall=nan_to_num(sub_item["metric_peak_hload_shortfall"]),
                        capex=nan_to_num(sub_item["metric_capex"]),
                        total_gas_import_cost=nan_to_num(sub_item["metric_total_gas_import_cost"]),
                        total_electricity_import_cost=nan_to_num(sub_item["metric_total_electricity_import_cost"]),
                        total_electricity_export_gain=nan_to_num(sub_item["metric_total_electricity_export_gain"]),
                        total_meter_cost=nan_to_num(sub_item["metric_total_meter_cost"]),
                        total_operating_cost=nan_to_num(sub_item["metric_total_operating_cost"]),
                        annualised_cost=nan_to_num(sub_item["metric_annualised_cost"]),
                        total_net_present_value=nan_to_num(sub_item["metric_total_net_present_value"]),
                        total_scope_1_emissions=nan_to_num(sub_item["metric_total_scope_1_emissions"]),
                        total_scope_2_emissions=nan_to_num(sub_item["metric_total_scope_2_emissions"]),
                        total_combined_carbon_emissions=nan_to_num(sub_item["metric_total_combined_carbon_emissions"]),
                        scenario_environmental_impact_score=nan_to_num(sub_item["metric_scenario_environmental_impact_score"]),
                        scenario_environmental_impact_grade=Grade[sub_item["metric_scenario_environmental_impact_grade"]]
                        if sub_item["metric_scenario_environmental_impact_grade"]
                        else None,
                        scenario_capex_breakdown=capex_breakdown_from_json(sub_item["scenario_capex_breakdown"]),
                        # baseline metrics
                        baseline_gas_used=nan_to_num(sub_item["metric_baseline_gas_used"]),
                        baseline_electricity_imported=nan_to_num(sub_item["metric_baseline_electricity_imported"]),
                        baseline_electricity_generated=nan_to_num(sub_item["metric_baseline_electricity_generated"]),
                        baseline_electricity_exported=nan_to_num(sub_item["metric_baseline_electricity_exported"]),
                        baseline_electricity_curtailed=nan_to_num(sub_item["metric_baseline_electricity_curtailed"]),
                        baseline_electricity_used=nan_to_num(sub_item["metric_baseline_electricity_used"]),
                        baseline_electrical_shortfall=nan_to_num(sub_item["metric_baseline_electrical_shortfall"]),
                        baseline_heat_load=nan_to_num(sub_item["metric_baseline_heat_load"]),
                        baseline_dhw_load=nan_to_num(sub_item["metric_baseline_dhw_load"]),
                        baseline_ch_load=nan_to_num(sub_item["metric_baseline_ch_load"]),
                        baseline_heat_shortfall=nan_to_num(sub_item["metric_baseline_heat_shortfall"]),
                        baseline_ch_shortfall=nan_to_num(sub_item["metric_baseline_ch_shortfall"]),
                        baseline_dhw_shortfall=nan_to_num(sub_item["metric_baseline_dhw_shortfall"]),
                        baseline_peak_hload_shortfall=nan_to_num(sub_item["metric_baseline_peak_hload_shortfall"]),
                        baseline_gas_import_cost=nan_to_num(sub_item["metric_baseline_gas_import_cost"]),
                        baseline_electricity_import_cost=nan_to_num(sub_item["metric_baseline_electricity_import_cost"]),
                        baseline_electricity_export_gain=nan_to_num(sub_item["metric_baseline_electricity_export_gain"]),
                        baseline_meter_cost=nan_to_num(sub_item["metric_baseline_meter_cost"]),
                        baseline_operating_cost=nan_to_num(sub_item["metric_baseline_operating_cost"]),
                        baseline_net_present_value=nan_to_num(sub_item["metric_baseline_net_present_value"]),
                        baseline_scope_1_emissions=nan_to_num(sub_item["metric_baseline_scope_1_emissions"]),
                        baseline_scope_2_emissions=nan_to_num(sub_item["metric_baseline_scope_2_emissions"]),
                        baseline_combined_carbon_emissions=nan_to_num(sub_item["metric_baseline_combined_carbon_emissions"]),
                        baseline_environmental_impact_score=nan_to_num(sub_item["metric_baseline_environmental_impact_score"]),
                        baseline_environmental_impact_grade=Grade[sub_item["metric_baseline_environmental_impact_grade"]]
                        if sub_item["metric_baseline_environmental_impact_grade"]
                        else None,
                    ),
                )
                for sub_item in item["site_results"]
                if sub_item is not None
            ]
            if item["site_results"] != [None]
            else None,
        )
        for item in res
    ]

    curated_results = await get_curated_results(task_id.task_id, pool)
    highlighted_results = pick_highlighted_results(portfolio_results, curated_results)
    search_spaces = await get_gui_site_range(task_id=task_id, pool=pool)
    search_info = get_search_info(search_spaces)

    for site_id, search_space in search_spaces.items():
        if site_id not in bundle_hints:
            # If we didn't get any hints, then skip this site and just return the indices
            continue
        search_spaces[site_id] = patch_hints_into_site_range(search_space, bundle_hints[site_id])

    return OptimisationResultsResponse(
        portfolio_results=portfolio_results,
        highlighted_results=highlighted_results,
        hints=bundle_hints,
        search_spaces=search_spaces,
        search_info=search_info,
    )


@router.post("/list-optimisation-tasks")
async def list_optimisation_tasks(pool: DatabasePoolDep, request: OptimisationTaskListRequest) -> OptimisationTaskListResponse:
    """
    Get all the optimisation tasks for a given client.

    We return these from most to least recent.

    Parameters
    ----------
    client_id

    Returns
    -------
    results

    """
    res = await pool.fetch(
        """
        WITH base AS (
            SELECT
                tc.task_id,
                tc.client_id,
                tc.task_name,
                tc.created_at AS created_at,
                ARRAY (
                    SELECT jsonb_array_elements_text(
                        COALESCE(tc.objectives, '[]'::jsonb)
                    )
                ) AS objectives,
                tc.epoch_version as epoch_version,
                ANY_VALUE(tr.n_evals)   AS n_evals,
                COUNT(pr.task_id)       AS n_saved,
                ANY_VALUE(tr.exec_time) AS exec_time
            FROM optimisation.task_config AS tc
            LEFT JOIN optimisation.task_results AS tr
                ON tr.task_id = tc.task_id
            LEFT JOIN optimisation.portfolio_results AS pr
                ON tc.task_id = pr.task_id
            WHERE tc.client_id = $1
            GROUP BY
                tc.task_id,
                tc.client_id,
                tc.task_name,
                tc.created_at,
                tc.objectives,
                tc.epoch_version
        )
        SELECT
            base.*,
            COUNT(*) OVER () AS total_results
        FROM base
        ORDER BY base.created_at DESC
        LIMIT $2
        OFFSET $3
        """,
        request.client_id,
        request.limit,
        request.offset,
    )

    result_count = res[0]["total_results"] if res else 0

    return OptimisationTaskListResponse(
        tasks=[
            OptimisationTaskListEntry(
                task_id=item["task_id"],
                task_name=item["task_name"],
                n_evals=item["n_evals"],
                n_saved=item["n_saved"],
                exec_time=item["exec_time"],
                created_at=item["created_at"],
                epoch_version=item["epoch_version"],
                objectives=item["objectives"],
            )
            for item in res
        ],
        total_results=result_count,
    )


@router.post("/add-optimisation-results")
async def add_optimisation_results(pool: DatabasePoolDep, opt_result: OptimisationResultEntry) -> None:
    """
    Add a set of optimisation results into the database.

    This must include the ID of the task which you inserted earlier with `add-optimisation-task`.
    You may add multiple OptimisationResults in a single call, which might include the top N results
    for a specific task.
    This will allow you to insert multiple results with the same TaskID, so may result in duplicates (but this is
    specifically handy to insert results in batches if you'd like).

    Parameters
    ----------
    portfolio
        An OptimisationResult with objective values (capex, annualised_cost, etc.) bundled together,
        and solutions (EPOCH single run parameter dict e.g. `{ESS_Capacity: 100, ...}`). The solutions
        dictionary will be relatively large, and is stored as a JSONB object in the database.

    Raises
    ------
    HTTPException(400)
        If there's a problem with the task or portfolio results.

    Returns
    -------
    200, OK
        If all was uploaded correctly.
    """
    async with pool.acquire() as conn, conn.transaction():
        if opt_result.portfolio:
            # Note that we don't add the specific site results here;
            # those are stored in a separate table.
            try:
                await conn.copy_records_to_table(
                    schema_name="optimisation",
                    table_name="portfolio_results",
                    records=zip(
                        [item.task_id for item in opt_result.portfolio],
                        [item.portfolio_id for item in opt_result.portfolio],
                        [item.is_feasible for item in opt_result.portfolio],
                        [item.metrics.meter_balance for item in opt_result.portfolio],
                        [item.metrics.operating_balance for item in opt_result.portfolio],
                        [item.metrics.cost_balance for item in opt_result.portfolio],
                        [item.metrics.npv_balance for item in opt_result.portfolio],
                        [item.metrics.payback_horizon for item in opt_result.portfolio],
                        [item.metrics.return_on_investment for item in opt_result.portfolio],
                        [item.metrics.carbon_balance_scope_1 for item in opt_result.portfolio],
                        [item.metrics.carbon_balance_scope_2 for item in opt_result.portfolio],
                        [item.metrics.carbon_balance_total for item in opt_result.portfolio],
                        [item.metrics.carbon_cost for item in opt_result.portfolio],
                        [item.metrics.total_gas_used for item in opt_result.portfolio],
                        [item.metrics.total_electricity_imported for item in opt_result.portfolio],
                        [item.metrics.total_electricity_generated for item in opt_result.portfolio],
                        [item.metrics.total_electricity_exported for item in opt_result.portfolio],
                        [item.metrics.total_electricity_curtailed for item in opt_result.portfolio],
                        [item.metrics.total_electricity_used for item in opt_result.portfolio],
                        [item.metrics.total_electrical_shortfall for item in opt_result.portfolio],
                        [item.metrics.total_heat_load for item in opt_result.portfolio],
                        [item.metrics.total_dhw_load for item in opt_result.portfolio],
                        [item.metrics.total_ch_load for item in opt_result.portfolio],
                        [item.metrics.total_heat_shortfall for item in opt_result.portfolio],
                        [item.metrics.total_ch_shortfall for item in opt_result.portfolio],
                        [item.metrics.total_dhw_shortfall for item in opt_result.portfolio],
                        [item.metrics.peak_hload_shortfall for item in opt_result.portfolio],
                        [item.metrics.capex for item in opt_result.portfolio],
                        [item.metrics.total_gas_import_cost for item in opt_result.portfolio],
                        [item.metrics.total_electricity_import_cost for item in opt_result.portfolio],
                        [item.metrics.total_electricity_export_gain for item in opt_result.portfolio],
                        [item.metrics.total_meter_cost for item in opt_result.portfolio],
                        [item.metrics.total_operating_cost for item in opt_result.portfolio],
                        [item.metrics.annualised_cost for item in opt_result.portfolio],
                        [item.metrics.total_net_present_value for item in opt_result.portfolio],
                        [item.metrics.total_scope_1_emissions for item in opt_result.portfolio],
                        [item.metrics.total_scope_2_emissions for item in opt_result.portfolio],
                        [item.metrics.total_combined_carbon_emissions for item in opt_result.portfolio],
                        [item.metrics.baseline_gas_used for item in opt_result.portfolio],
                        [item.metrics.baseline_electricity_imported for item in opt_result.portfolio],
                        [item.metrics.baseline_electricity_generated for item in opt_result.portfolio],
                        [item.metrics.baseline_electricity_exported for item in opt_result.portfolio],
                        [item.metrics.baseline_electricity_curtailed for item in opt_result.portfolio],
                        [item.metrics.baseline_electricity_used for item in opt_result.portfolio],
                        [item.metrics.baseline_electrical_shortfall for item in opt_result.portfolio],
                        [item.metrics.baseline_heat_load for item in opt_result.portfolio],
                        [item.metrics.baseline_dhw_load for item in opt_result.portfolio],
                        [item.metrics.baseline_ch_load for item in opt_result.portfolio],
                        [item.metrics.baseline_heat_shortfall for item in opt_result.portfolio],
                        [item.metrics.baseline_ch_shortfall for item in opt_result.portfolio],
                        [item.metrics.baseline_dhw_shortfall for item in opt_result.portfolio],
                        [item.metrics.baseline_peak_hload_shortfall for item in opt_result.portfolio],
                        [item.metrics.baseline_gas_import_cost for item in opt_result.portfolio],
                        [item.metrics.baseline_electricity_import_cost for item in opt_result.portfolio],
                        [item.metrics.baseline_electricity_export_gain for item in opt_result.portfolio],
                        [item.metrics.baseline_meter_cost for item in opt_result.portfolio],
                        [item.metrics.baseline_operating_cost for item in opt_result.portfolio],
                        [item.metrics.baseline_net_present_value for item in opt_result.portfolio],
                        [item.metrics.baseline_scope_1_emissions for item in opt_result.portfolio],
                        [item.metrics.baseline_scope_2_emissions for item in opt_result.portfolio],
                        [item.metrics.baseline_combined_carbon_emissions for item in opt_result.portfolio],
                        strict=True,
                    ),
                    columns=[
                        "task_id",
                        "portfolio_id",
                        "is_feasible",
                        "metric_meter_balance",
                        "metric_operating_balance",
                        "metric_cost_balance",
                        "metric_npv_balance",
                        "metric_payback_horizon",
                        "metric_return_on_investment",
                        "metric_carbon_balance_scope_1",
                        "metric_carbon_balance_scope_2",
                        "metric_combined_carbon_balance",
                        "metric_carbon_cost",
                        "metric_total_gas_used",
                        "metric_total_electricity_imported",
                        "metric_total_electricity_generated",
                        "metric_total_electricity_exported",
                        "metric_total_electricity_curtailed",
                        "metric_total_electricity_used",
                        "metric_total_electrical_shortfall",
                        "metric_total_heat_load",
                        "metric_total_dhw_load",
                        "metric_total_ch_load",
                        "metric_total_heat_shortfall",
                        "metric_total_ch_shortfall",
                        "metric_total_dhw_shortfall",
                        "metric_peak_hload_shortfall",
                        "metric_capex",
                        "metric_total_gas_import_cost",
                        "metric_total_electricity_import_cost",
                        "metric_total_electricity_export_gain",
                        "metric_total_meter_cost",
                        "metric_total_operating_cost",
                        "metric_annualised_cost",
                        "metric_total_net_present_value",
                        "metric_total_scope_1_emissions",
                        "metric_total_scope_2_emissions",
                        "metric_total_combined_carbon_emissions",
                        "metric_baseline_gas_used",
                        "metric_baseline_electricity_imported",
                        "metric_baseline_electricity_generated",
                        "metric_baseline_electricity_exported",
                        "metric_baseline_electricity_curtailed",
                        "metric_baseline_electricity_used",
                        "metric_baseline_electrical_shortfall",
                        "metric_baseline_heat_load",
                        "metric_baseline_dhw_load",
                        "metric_baseline_ch_load",
                        "metric_baseline_heat_shortfall",
                        "metric_baseline_ch_shortfall",
                        "metric_baseline_dhw_shortfall",
                        "metric_baseline_peak_hload_shortfall",
                        "metric_baseline_gas_import_cost",
                        "metric_baseline_electricity_import_cost",
                        "metric_baseline_electricity_export_gain",
                        "metric_baseline_meter_cost",
                        "metric_baseline_operating_cost",
                        "metric_baseline_net_present_value",
                        "metric_baseline_scope_1_emissions",
                        "metric_baseline_scope_2_emissions",
                        "metric_baseline_combined_carbon_emissions",
                    ],
                )
            except asyncpg.exceptions.ForeignKeyViolationError as ex:
                raise HTTPException(
                    400,
                    f"task_id={opt_result.portfolio[0].task_id} does not have an associated task config."
                    + "You should have added it via /add-optimisation-task beforehand.",
                ) from ex

            for pf in opt_result.portfolio:
                if not pf.site_results:
                    # No site results here, so skip it.
                    continue
                await conn.copy_records_to_table(
                    schema_name="optimisation",
                    table_name="site_results",
                    records=zip(
                        [item.site_id for item in pf.site_results],
                        [item.portfolio_id for item in pf.site_results],
                        [json.dumps(jsonable_encoder(item.scenario)) for item in pf.site_results],
                        [item.is_feasible for item in pf.site_results],
                        [item.metrics.meter_balance for item in pf.site_results],
                        [item.metrics.operating_balance for item in pf.site_results],
                        [item.metrics.cost_balance for item in pf.site_results],
                        [item.metrics.npv_balance for item in pf.site_results],
                        [item.metrics.payback_horizon for item in pf.site_results],
                        [item.metrics.return_on_investment for item in pf.site_results],
                        [item.metrics.carbon_balance_scope_1 for item in pf.site_results],
                        [item.metrics.carbon_balance_scope_2 for item in pf.site_results],
                        [item.metrics.carbon_balance_total for item in pf.site_results],
                        [item.metrics.carbon_cost for item in pf.site_results],
                        [item.metrics.total_gas_used for item in pf.site_results],
                        [item.metrics.total_electricity_imported for item in pf.site_results],
                        [item.metrics.total_electricity_generated for item in pf.site_results],
                        [item.metrics.total_electricity_exported for item in pf.site_results],
                        [item.metrics.total_electricity_curtailed for item in pf.site_results],
                        [item.metrics.total_electricity_used for item in pf.site_results],
                        [item.metrics.total_electrical_shortfall for item in pf.site_results],
                        [item.metrics.total_heat_load for item in pf.site_results],
                        [item.metrics.total_dhw_load for item in pf.site_results],
                        [item.metrics.total_ch_load for item in pf.site_results],
                        [item.metrics.total_heat_shortfall for item in pf.site_results],
                        [item.metrics.total_ch_shortfall for item in pf.site_results],
                        [item.metrics.total_dhw_shortfall for item in pf.site_results],
                        [item.metrics.peak_hload_shortfall for item in pf.site_results],
                        [item.metrics.capex for item in pf.site_results],
                        [item.metrics.total_gas_import_cost for item in pf.site_results],
                        [item.metrics.total_electricity_import_cost for item in pf.site_results],
                        [item.metrics.total_electricity_export_gain for item in pf.site_results],
                        [item.metrics.total_meter_cost for item in pf.site_results],
                        [item.metrics.total_operating_cost for item in pf.site_results],
                        [item.metrics.annualised_cost for item in pf.site_results],
                        [item.metrics.total_net_present_value for item in pf.site_results],
                        [item.metrics.total_scope_1_emissions for item in pf.site_results],
                        [item.metrics.total_scope_2_emissions for item in pf.site_results],
                        [item.metrics.total_combined_carbon_emissions for item in pf.site_results],
                        [item.metrics.scenario_environmental_impact_score for item in pf.site_results],
                        [item.metrics.scenario_environmental_impact_grade for item in pf.site_results],
                        [capex_breakdown_to_json(item.metrics.scenario_capex_breakdown) for item in pf.site_results],
                        [item.metrics.baseline_gas_used for item in pf.site_results],
                        [item.metrics.baseline_electricity_imported for item in pf.site_results],
                        [item.metrics.baseline_electricity_generated for item in pf.site_results],
                        [item.metrics.baseline_electricity_exported for item in pf.site_results],
                        [item.metrics.baseline_electricity_curtailed for item in pf.site_results],
                        [item.metrics.baseline_electricity_used for item in pf.site_results],
                        [item.metrics.baseline_electrical_shortfall for item in pf.site_results],
                        [item.metrics.baseline_heat_load for item in pf.site_results],
                        [item.metrics.baseline_dhw_load for item in pf.site_results],
                        [item.metrics.baseline_ch_load for item in pf.site_results],
                        [item.metrics.baseline_heat_shortfall for item in pf.site_results],
                        [item.metrics.baseline_ch_shortfall for item in pf.site_results],
                        [item.metrics.baseline_dhw_shortfall for item in pf.site_results],
                        [item.metrics.baseline_peak_hload_shortfall for item in pf.site_results],
                        [item.metrics.baseline_gas_import_cost for item in pf.site_results],
                        [item.metrics.baseline_electricity_import_cost for item in pf.site_results],
                        [item.metrics.baseline_electricity_export_gain for item in pf.site_results],
                        [item.metrics.baseline_meter_cost for item in pf.site_results],
                        [item.metrics.baseline_operating_cost for item in pf.site_results],
                        [item.metrics.baseline_net_present_value for item in pf.site_results],
                        [item.metrics.baseline_scope_1_emissions for item in pf.site_results],
                        [item.metrics.baseline_scope_2_emissions for item in pf.site_results],
                        [item.metrics.baseline_combined_carbon_emissions for item in pf.site_results],
                        [item.metrics.baseline_environmental_impact_score for item in pf.site_results],
                        [item.metrics.baseline_environmental_impact_grade for item in pf.site_results],
                        strict=True,
                    ),
                    columns=[
                        "site_id",
                        "portfolio_id",
                        "scenario",
                        "is_feasible",
                        "metric_meter_balance",
                        "metric_operating_balance",
                        "metric_cost_balance",
                        "metric_npv_balance",
                        "metric_payback_horizon",
                        "metric_return_on_investment",
                        "metric_carbon_balance_scope_1",
                        "metric_carbon_balance_scope_2",
                        "metric_combined_carbon_balance",
                        "metric_carbon_cost",
                        "metric_total_gas_used",
                        "metric_total_electricity_imported",
                        "metric_total_electricity_generated",
                        "metric_total_electricity_exported",
                        "metric_total_electricity_curtailed",
                        "metric_total_electricity_used",
                        "metric_total_electrical_shortfall",
                        "metric_total_heat_load",
                        "metric_total_dhw_load",
                        "metric_total_ch_load",
                        "metric_total_heat_shortfall",
                        "metric_total_ch_shortfall",
                        "metric_total_dhw_shortfall",
                        "metric_peak_hload_shortfall",
                        "metric_capex",
                        "metric_total_gas_import_cost",
                        "metric_total_electricity_import_cost",
                        "metric_total_electricity_export_gain",
                        "metric_total_meter_cost",
                        "metric_total_operating_cost",
                        "metric_annualised_cost",
                        "metric_total_net_present_value",
                        "metric_total_scope_1_emissions",
                        "metric_total_scope_2_emissions",
                        "metric_total_combined_carbon_emissions",
                        "metric_scenario_environmental_impact_score",
                        "metric_scenario_environmental_impact_grade",
                        "scenario_capex_breakdown",
                        "metric_baseline_gas_used",
                        "metric_baseline_electricity_imported",
                        "metric_baseline_electricity_generated",
                        "metric_baseline_electricity_exported",
                        "metric_baseline_electricity_curtailed",
                        "metric_baseline_electricity_used",
                        "metric_baseline_electrical_shortfall",
                        "metric_baseline_heat_load",
                        "metric_baseline_dhw_load",
                        "metric_baseline_ch_load",
                        "metric_baseline_heat_shortfall",
                        "metric_baseline_ch_shortfall",
                        "metric_baseline_dhw_shortfall",
                        "metric_baseline_peak_hload_shortfall",
                        "metric_baseline_gas_import_cost",
                        "metric_baseline_electricity_import_cost",
                        "metric_baseline_electricity_export_gain",
                        "metric_baseline_meter_cost",
                        "metric_baseline_operating_cost",
                        "metric_baseline_net_present_value",
                        "metric_baseline_scope_1_emissions",
                        "metric_baseline_scope_2_emissions",
                        "metric_baseline_combined_carbon_emissions",
                        "metric_baseline_environmental_impact_score",
                        "metric_baseline_environmental_impact_grade",
                    ],
                )

        if opt_result.tasks:
            await conn.copy_records_to_table(
                table_name="task_results",
                schema_name="optimisation",
                records=zip(
                    [item.task_id for item in opt_result.tasks],
                    [item.n_evals for item in opt_result.tasks],
                    [item.exec_time for item in opt_result.tasks],
                    [item.completed_at for item in opt_result.tasks],
                    strict=True,
                ),
                columns=["task_id", "n_evals", "exec_time", "completed_at"],
            )


@router.post("/add-optimisation-task")
async def add_optimisation_task(task_config: TaskConfig, pool: DatabasePoolDep) -> TaskConfig:
    """
    Add the details of an optimisation task into the database.

    You should do this when a task enters the queue (or potentially when it starts executing),
    and describe the parameters put in to the task here.

    Parameters
    ----------
    *task_config*
        Task configuration, featuring a unique ID, search space information (in `parameters`),
        and constraints (ideally split into `constraints_min` and `constraints_max`)

    Returns
    -------
    *task_config*
        A copy of the task config you just sent, after being put into the database.

    Raises
    ------
    *HTTPException*
        If the key already exists in the database.
    """
    async with pool.acquire() as conn, conn.transaction():
        try:
            await conn.execute(
                """
                    INSERT INTO
                        optimisation.task_config (
                            task_id,
                            client_id,
                            task_name,
                            optimiser_type,
                            optimiser_hyperparameters,
                            created_at,
                            objectives,
                            portfolio_constraints,
                            epoch_version)
                        VALUES (
                        $1,
                        $2,
                        $3,
                        $4,
                        $5,
                        $6,
                        $7,
                        $8,
                        $9)""",
                task_config.task_id,
                task_config.client_id,
                task_config.task_name,
                task_config.optimiser.name,
                json.dumps(jsonable_encoder(task_config.optimiser.hyperparameters)),
                task_config.created_at,
                json.dumps(jsonable_encoder(task_config.objectives)),
                json.dumps(jsonable_encoder(task_config.portfolio_constraints)),
                task_config.epoch_version,
            )

        except asyncpg.exceptions.UniqueViolationError as ex:
            raise HTTPException(400, f"TaskID {task_config.task_id} already exists in the database.") from ex

        await conn.copy_records_to_table(
            schema_name="optimisation",
            table_name="site_task_config",
            records=[
                (
                    task_config.task_id,
                    site_id,
                    bundle_id,
                    json.dumps(jsonable_encoder(task_config.site_constraints[site_id])),  # type: ignore
                    json.dumps(jsonable_encoder(task_config.portfolio_range[site_id])),
                )
                for site_id, bundle_id in task_config.bundle_ids.items()
            ],
            columns=["task_id", "site_id", "bundle_id", "site_constraints", "site_range"],
        )

    return task_config


@router.post("/get-result-configuration")
async def get_result_configuration(result_id: ResultID, pool: DatabasePoolDep) -> result_repro_config_t:
    """
    Return the configuration that was used to produce a given result.

    Parameters
    ----------
    result_id
        The result_id for a result in the database that you want to reproduce

    Returns
    -------
        All of the configuration data necessary to reproduce this simulation
    """
    rows = await pool.fetch(
        """
        SELECT
            stc.site_data,
            stc.site_id,
            stc.bundle_id,
            sr.scenario
        FROM
            optimisation.site_results AS sr
        LEFT JOIN
            optimisation.portfolio_results AS pr
            ON sr.portfolio_id = pr.portfolio_id
        LEFT JOIN
            optimisation.site_task_config AS stc
            ON pr.task_id = stc.task_id
        WHERE
            sr.portfolio_id = $1 AND stc.site_id = sr.site_id
        """,
        result_id.result_id,
    )

    if rows is None:
        raise HTTPException(400, f"No task configuration exists for result with id {result_id.result_id}")

    bundle_ids = {}
    scenarios = {}

    for row in rows:
        site_id = row["site_id"]
        bundle_ids[site_id] = row["bundle_id"]
        scenarios[site_id] = json.loads(row["scenario"])

    if any(value is None for value in bundle_ids.values()):
        site_datas: dict[str, SiteDataEntry] = {}
        for row in rows:
            site_datas[site_id] = json.loads(row["site_data"])

        return LegacyResultReproConfig(portfolio_id=result_id.result_id, task_data=scenarios, site_data=site_datas)

    return NewResultReproConfig(portfolio_id=result_id.result_id, task_data=scenarios, bundle_ids=bundle_ids)


@router.post("/add-curated-result", tags=["highlight"])
async def add_curated_result(addRequest: AddCuratedResultRequest, pool: DatabasePoolDep) -> CuratedResult:
    """
    Add a portfolio result to the curated results table so that it can be returned by the results highlighting logic.

    Parameters
    ----------
    addRequest
        The task_id, portfolio_id pair and a display name
    pool
        The database pool

    Returns
    -------
    The curated result that has been added.
    """
    result = CuratedResult(
        highlight_id=uuid7(),
        task_id=addRequest.task_id,
        portfolio_id=addRequest.portfolio_id,
        display_name=addRequest.display_name,
    )

    async with pool.acquire() as conn, conn.transaction():
        try:
            await conn.execute(
                """
                INSERT INTO optimisation.curated_results (
                    highlight_id,
                    task_id,
                    portfolio_id,
                    submitted_at,
                    display_name)
                    VALUES (
                    $1,
                    $2,
                    $3,
                    $4,
                    $5)""",
                result.highlight_id,
                result.task_id,
                result.portfolio_id,
                result.submitted_at,
                result.display_name,
            )
        except asyncpg.exceptions.ForeignKeyViolationError as ex:
            raise HTTPException(400, "No such task_id / portfolio_id.") from ex

    return result


@router.post("/list-curated-results", tags=["highlight"])
async def list_curated_results(pool: DatabasePoolDep, task_id: dataset_id_t | None = None) -> ListCuratedResultsResponse:
    """
    List all curated results, optionally filtered by a task_id.

    Results are sorted by submission time. Most recent first.

    Parameters
    ----------
    task_id
        A task_id to filter the curated results on. Use None to see all curated results.
    pool

    Returns
    -------
    A list of curated results.
    """
    results = await get_curated_results(task_id, pool)
    return ListCuratedResultsResponse(curated_results=results)


@router.post("/remove-curated-result", tags=["highlight"])
async def remove_curated_result(highlight_id: dataset_id_t, pool: DatabasePoolDep) -> None:
    """
    Remove a curated result from the curated results table.

    Parameters
    ----------
    highlight_id
        A unique ID to identify this curated result. Retrieve this with /list-curated-results
    pool

    Returns
    -------
    None

    """
    async with pool.acquire() as conn, conn.transaction():
        res = await conn.execute(
            """
            DELETE FROM optimisation.curated_results
            WHERE highlight_id = $1
            """,
            highlight_id,
        )

        if res == "DELETE 0":
            raise HTTPException(404, f"No curated result with highlight_id={highlight_id}")
