"""
Functions for calculation interesting days in the output of a simulation.

Interesting days have a reason for being interesting, and start & end timestamps.
"""

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from pydantic import BaseModel, Field

from app.models.epoch_types.report_data_type import ReportData
from app.models.epoch_types.task_data_type import TaskData
from app.models.simulate import DayOfInterest, DayOfInterestType
from app.models.site_data import EpochSiteData


class DayGrouping(BaseModel):
    """Precomputed mapping from each timestep to its datetime."""

    codes: NDArray[np.int32] = Field(..., description="int codes per sample (0..n_days-1)")
    days: pd.DatetimeIndex = Field(..., description="unique UTC-normalized days (len == n_days)")

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


def _ensure_utc_index(timestamps: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Return a tz-aware UTC index."""
    if timestamps.tz is None:
        return timestamps.tz_localize("UTC")
    return timestamps.tz_convert("UTC")


def _build_day_grouping(timestamps: pd.DatetimeIndex) -> DayGrouping:
    """
    Process the list of timestamps, associating each one with a 'code' corresponding to the day it belongs to.

    Parameters
    ----------
    timestamps
        The timestamps for each entry in the timeseries

    Returns
    -------
        A DayGrouping object that maps each timestamp to the day it belongs to.
    """
    ts = _ensure_utc_index(timestamps)
    days = ts.normalize()  # midnight UTC for each sample
    codes, uniques = pd.factorize(days, sort=True)
    return DayGrouping(codes=codes.astype(np.int32, copy=False), days=pd.DatetimeIndex(uniques))


def _best_day_by_sum(
        values: NDArray[np.float32] | list[float],
        groups: DayGrouping, require_positive: bool = True) -> tuple[pd.Timestamp, pd.Timestamp] | None:
    """
    Group values in the provided timeseries per day and return the maximum.

    Parameters
    ----------
    values
        A timeseries - directly from, or derived from, epoch reporting
    groups
        Mapping of timestep indices to DateTimes

    require_positive
        Whether to require that the best day is greater than zero or not

    Returns
    -------
        A start and end timestamp for the best day

    """
    weights = np.asarray(values, dtype=float)
    if weights.size == 0:
        return None

    # NaNs should not poison the daily sums
    weights = np.nan_to_num(weights, nan=0.0)

    # bincount sums up all the entries in the timeseries (weights) into bins representing each day (groups.codes)
    daily = np.bincount(groups.codes, weights=weights, minlength=len(groups.days))

    if require_positive:
        valid = daily > 0
        if not np.any(valid):
            return None
        # Argmax over the full array is fine since we already ensured at least one positive
        best_i = int(np.argmax(daily))
    else:
        # If not requiring positive, still handle the corner case all zeros -> return None
        if not np.any(daily):
            return None
        best_i = int(np.argmax(daily))

    best_day = groups.days[best_i]
    return best_day, best_day + pd.Timedelta(days=1)


def detect_days_of_interest(
    report_data: ReportData, site_data: EpochSiteData, task_data: TaskData, timestamps: pd.DatetimeIndex
) -> list[DayOfInterest]:
    """
    Detect some interest days in the calculated report data.

    These days are generally the maxima or minima of various output time series over a 24 hour period.
    We'll only highlight a day if there is a day to highlight, so you might get an empty list if there are no interesting days.

    Parameters
    ----------
    report_data
        Calculated time series from an EPOCH simulation
    site_data
        Additional time series about cost, generation etc
    task_data
        Configuration for this simulation

    Returns
    -------
    list[DaysOfInterest]
        A potentially empty list, where a day of interest has a reason, start_ts and end_ts.
    """
    days = []

    groups = _build_day_grouping(timestamps)

    if max_solar := detect_max_solar_day(report_data=report_data, groups=groups):
        days.append(max_solar)

    if max_heating := detect_max_heating_day(report_data=report_data, groups=groups):
        days.append(max_heating)

    if max_ess := detect_max_ess_day(report_data=report_data, groups=groups):
        days.append(max_ess)

    if max_cost := detect_max_cost_day(report_data=report_data, site_data=site_data, task_data=task_data, groups=groups):
        days.append(max_cost)

    if max_eload := detect_max_eload_day(report_data=report_data, groups=groups):
        days.append(max_eload)

    if max_heat_shortfall := detect_max_heat_shortfall_day(report_data=report_data, groups=groups):
        days.append(max_heat_shortfall)

    if max_elec_shortfall := detect_max_elec_shortfall_day(report_data=report_data, groups=groups):
        days.append(max_elec_shortfall)

    if max_dhw := detect_max_dhw_usage_day(report_data=report_data, groups=groups):
        days.append(max_dhw)

    return days


def detect_max_heat_shortfall_day(report_data: ReportData, groups: DayGrouping) -> DayOfInterest | None:
    """
    Detect the day with the maximum heat shortfall.

    Parameters
    ----------
    report_data
        Output of EPOCH including Heat_shortfall (returns None if that is None)
    groups
        Mapping of timestep indices to DateTimes

    Returns
    -------
    DayOfInterest
        A start_ts, end_ts and type for the calendar day with most heat shortfall.
    None
        If we didn't find a day with any heat shortfall.
    """
    if not report_data.Heat_shortfall:
        return None

    res = _best_day_by_sum(report_data.Heat_shortfall, groups)
    if res is None:
        return None

    start_ts, end_ts = res

    return DayOfInterest(
        day_type=DayOfInterestType.MaxHeatShortfall,
        name="Maximum Heat Shortfall",
        start_ts=start_ts,
        end_ts=end_ts,
    )


def detect_max_solar_day(report_data: ReportData, groups: DayGrouping) -> DayOfInterest | None:
    """
    Detect the day with the maximum solar generation.

    Parameters
    ----------
    report_data
        Output of EPOCH including PVacGen (returns None if that is None)
    groups
        Mapping of timestep indices to DateTimes

    Returns
    -------
    DayOfInterest
        A start_ts, end_ts and type for the calendar day with most solar generation.
    None
        If we didn't find a day with any solar generation.
    """
    if report_data.PVacGen is None:
        return None
    res = _best_day_by_sum(report_data.PVacGen, groups)
    if res is None:
        return None
    start_ts, end_ts = res
    return DayOfInterest(
        day_type=DayOfInterestType.MaxGeneration,
        name="Maximum Solar Generation",
        start_ts=start_ts,
        end_ts=end_ts,
    )


def detect_max_heating_day(report_data: ReportData, groups: DayGrouping) -> DayOfInterest | None:
    """
    Detect the day with the maximum total heat load.

    Parameters
    ----------
    report_data
        Output of EPOCH including Heatload (returns None if that is None)
    groups
        Mapping of timestep indices to DateTimes

    Returns
    -------
    DayOfInterest
        A start_ts, end_ts and type for the calendar day with most heat load.
    None
        If we didn't find a day with any heat load.
    """
    if not report_data.Heatload:
        return None

    res = _best_day_by_sum(report_data.Heatload, groups)
    if res is None:
        return None
    start_ts, end_ts = res
    return DayOfInterest(
        day_type=DayOfInterestType.MaxHeating,
        name="Maximum Heating Load",
        start_ts=start_ts,
        end_ts=end_ts,
    )


def detect_max_ess_day(report_data: ReportData, groups: DayGrouping) -> DayOfInterest | None:
    """
    Detect the day with the maximum total battery throughput.

    The battery throughput is the absolute value of the charge and discharge on the battery.


    Parameters
    ----------
    report_data
        Output of EPOCH including ESS_charge and ESS_discharge (returns None if that is None)
    groups
        Mapping of timestep indices to DateTimes

    Returns
    -------
    DayOfInterest
        A start_ts, end_ts and type for the calendar day with most battery throughput load.
    None
        If we didn't find a day with any battery load.
    """
    if not report_data.ESS_charge or not report_data.ESS_discharge:
        return None
    ess_throughput = np.abs(np.asarray(report_data.ESS_charge)) + np.abs(np.asarray(report_data.ESS_discharge))

    res = _best_day_by_sum(ess_throughput, groups)
    if res is None:
        return None
    start_ts, end_ts = res
    return DayOfInterest(
        day_type=DayOfInterestType.MaxBatteryThroughput,
        name="Maximum Battery Throughput",
        start_ts=start_ts,
        end_ts=end_ts,
    )


def detect_max_cost_day(
    report_data: ReportData, site_data: EpochSiteData, task_data: TaskData, groups: DayGrouping
) -> DayOfInterest | None:
    """
    Detect the most expensive day.

    The most expensive day is where the chosen import tariff * consumption minus export is highest.

    Parameters
    ----------
    report_data
        Output of EPOCH including Grid Import and Export (returns None if they are None)
    site_data
        Site data including import tariffs
    task_data
        Task data including the specification of the import tariff

    groups
        Mapping of timestep indices to DateTimes

    Returns
    -------
    DayOfInterest
        A start_ts, end_ts and type for the calendar day with most import minus export costs.
    None
        If we didn't find a day with any grid costs.
    """
    if task_data.grid is None or task_data.grid.tariff_index is None:
        return None
    tariff_idx = task_data.grid.tariff_index
    tariff_arr = np.asarray(site_data.import_tariffs[tariff_idx])
    import_arr = np.asarray(report_data.Grid_Import)

    cost_arr = import_arr * tariff_arr
    if report_data.Grid_Export is not None and task_data.grid.export_tariff is not None:
        export_arr = np.asarray(report_data.Grid_Export)
        cost_arr -= export_arr * task_data.grid.export_tariff

    res = _best_day_by_sum(cost_arr, groups)
    if res is None:
        return None

    start_ts, end_ts = res
    return DayOfInterest(
        day_type=DayOfInterestType.MaxCost,
        name="Most Expensive Day",
        start_ts=start_ts,
        end_ts=end_ts
    )


def detect_max_eload_day(report_data: ReportData, groups: DayGrouping) -> DayOfInterest | None:
    """
    Detect the day with the maximum electrical demand.

    Calculated by summing all sources of electricity and subtracting any sinks.

    Parameters
    ----------
    report_data
        Output of EPOCH
    groups
        Mapping of timestep indices to DateTimes

    Returns
    -------
    DayOfInterest
        A start_ts, end_ts and type for the calendar day with the highest electrical load.
    None
        If we didn't find a day with any electrical load.
    """
    elec_sources = np.zeros(shape=groups.codes.shape, dtype=np.float32)
    elec_sinks = np.zeros(shape=groups.codes.shape, dtype=np.float32)
    if report_data.Grid_Import is not None:
        elec_sources += np.asarray(report_data.Grid_Import)
    if report_data.Actual_import_shortfall is not None:
        elec_sources += np.asarray(report_data.Actual_import_shortfall)
    if report_data.PVacGen is not None:
        elec_sources += np.asarray(report_data.PVacGen)
    if report_data.ESS_discharge is not None:
        elec_sources += np.asarray(report_data.ESS_discharge)

    if report_data.Grid_Export is not None:
        elec_sinks += np.asarray(report_data.Grid_Export)
    if report_data.Actual_curtailed_export is not None:
        elec_sinks += np.asarray(report_data.Actual_curtailed_export)
    if report_data.ESS_charge is not None:
        elec_sinks += np.asarray(report_data.ESS_charge)

    elec_usage = elec_sources - elec_sinks

    res = _best_day_by_sum(elec_usage, groups)

    if res is None:
        return None

    start_ts, end_ts = res

    return DayOfInterest(
        day_type=DayOfInterestType.MaxDemand,
        name="Maximum Electrical Load",
        start_ts=start_ts,
        end_ts=end_ts
    )


def detect_max_elec_shortfall_day(report_data: ReportData, groups: DayGrouping) -> DayOfInterest | None:
    """
    Detect the day with the maximum electrical shortfall.

    This is "import_shortfall" and doesn't handle electrical curtailment.

    Parameters
    ----------
    report_data
        Output of EPOCH including Actual_import_shortfall (returns None if that is None)
    groups
        Mapping of timestep indices to DateTimes

    Returns
    -------
    DayOfInterest
        A start_ts, end_ts and type for the calendar day with most electrical import shortfall.
    None
        If we didn't find a day with any electrical shortfall.
    """
    if report_data.Actual_import_shortfall is None:
        return None

    res = _best_day_by_sum(report_data.Actual_import_shortfall, groups)
    if res is None:
        return None

    start_ts, end_ts = res

    return DayOfInterest(
        day_type=DayOfInterestType.MaxImportShortfall,
        name="Maximum Electrical Load",
        start_ts=start_ts,
        end_ts=end_ts,
    )


def detect_max_dhw_usage_day(report_data: ReportData, groups: DayGrouping) -> DayOfInterest | None:
    """
    Detect the day with the maximum domestic hot water usage.

    This is DHW demand, and includes both that met from the cylinder and immersion.

    Parameters
    ----------
    report_data
        Output of EPOCH including DHW_demand (returns None if that is None)
    groups
        Mapping of timestep indices to DateTimes

    Returns
    -------
    DayOfInterest
        A start_ts, end_ts and type for the calendar day with most DHW demand.
    None
        If we didn't find a day with any DHW usage.
    """
    if report_data.DHW_demand is None:
        return None

    res = _best_day_by_sum(report_data.DHW_demand, groups)
    if res is None:
        return None

    start_ts, end_ts = res

    return DayOfInterest(
        day_type=DayOfInterestType.MaxDHWDemand,
        name="Maximum Hot Water Load",
        start_ts=start_ts,
        end_ts=end_ts,
    )
