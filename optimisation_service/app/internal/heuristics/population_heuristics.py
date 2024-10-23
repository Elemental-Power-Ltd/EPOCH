"""
Population heuristics for initialising EPOCH search spaces.
"""

import numpy as np
import pandas as pd


def estimate_ashp_hpower(
    heating_df: pd.DataFrame,
    ashp_input_df: pd.DataFrame,
    ashp_output_df: pd.DataFrame,
    air_temp_df: pd.DataFrame,
    ashp_mode: int,
    quantile: float = 0.99,
) -> float:
    """
    Estimate the air source heat pump electrical power rating.

    This will attempt to size a heat pump considering COP to meet the x% highest heat demand of the year.
    The electrical load is (heat load / cop) at each timestep in kW.
    Generally heat loads are sized for the 99th percentile, i.e. the heat pump must provide adequate heat on the 1% coldest day
    of the year.

    Parameters
    ----------
    heating_df
        EPOCH friendly heat load dataframe with Date, Start Time and HLoad1 columns.
    ashp_input_df
        Air source heat pump power draw dataframe in EPOCH format (air temp rows, setting columns)
    ashp_output_df
        Air source heat pump heat output dataframe in EPOCH format (air temp rows, setting columns)
    air_temp_df
        Air temperature dataframe in °C with Air-temp column
    ashp_mode
        Air source heat pump mode matching the column headers of the ASHP dataframes, this is either a weather compensation
        setting or a flow temperature.
    quantile
        Percentile worst head load to size for

    Returns
    -------
    Estimated heat pump electrical rating in kW
    """
    ashp_input_row = ashp_input_df[str(ashp_mode)].to_numpy()
    ashp_output_row = ashp_output_df[str(ashp_mode)].to_numpy()

    air_temps = air_temp_df["Air-temp"]
    ashp_inputs = np.interp(air_temps, ashp_input_df.index.to_numpy(), ashp_input_row)
    ashp_outputs = np.interp(air_temps, ashp_output_df.index.to_numpy(), ashp_output_row)

    cops = ashp_outputs / ashp_inputs

    # We want rating in kW, so if there was a heat load of 1kWh in a 30 minute timestep, that's a 2kW load.
    hload_times = pd.to_datetime(heating_df["Date"] + " 2024 " + heating_df["Start Time"], utc=True)

    timedeltas = np.pad(
        [item.to_timedelta64() for item in np.ediff1d(hload_times)], pad_width=(0, 1), mode="wrap"
    ) / np.timedelta64(1, "h")

    elec_loads = (heating_df["HLoad1"] / cops) / timedeltas
    return np.quantile(elec_loads, quantile)


def estimate_solar_pv(solar_df: pd.DataFrame, elec_df: pd.DataFrame, quantile: float = 0.75) -> float:
    """
    Estimate the solar PV array size for this site to cover a fraction of daily usage.

    This will size the RGen1 array to cover all electrical demand at x% of sunny timesteps, where x% is chosen by `quantile`.
    A sunny timestep has non-zero solar generation, but this can be very low (e.g. clear winter evenings).
    If quantile is set large this will significantly oversize the solar array as it attempts to cover all electrical usage.
    If quantile is small, the solar array will be closer to being sized for summer afternoons.

    Parameters
    ----------
    solar_df
        Potential solar output of a 1kWp array on this site, with "RGen1" column.
    elec_df
        Electrical load dataframe with "FixLoad1" column
    quantile
        What fraction of electrical loads during sunny days to attempt to cover

    Returns
    -------
    Estimated solar array size in kWp
    """
    is_nonzero_solar = solar_df["RGen1"] > 0
    required_solar = elec_df.loc[is_nonzero_solar, "FixLoad1"] / solar_df.loc[is_nonzero_solar, "RGen1"]
    return float(np.quantile(required_solar, quantile))


def estimate_battery_capacity(elec_df: pd.DataFrame, quantile: float = 0.75) -> float:
    """
    Estimate the required battery capacity to avoid peak time usage.

    This will select a battery size to cover the `quantile`% worst 16:00-19:00 period.
    Set `quantile` to 1 to cover the maximally bad 16:00-19:00 period.

    Parameters
    ----------
    elec_df
        EPOCH-friendly dataframe with "Date", "Start Time" and "FixLoad1" columns.
    quantile
        What fraction of days 16:00-19:00 period we should cover.

    Returns
    -------
    Estimated battery capacity for this site in kWh
    """
    time_of_day = np.array([float(item[0]) + float(item[1]) / 60 for item in elec_df["Start Time"].str.split(":")])
    is_peak = np.logical_and(time_of_day >= 16, time_of_day < 19)
    peak_elec = elec_df[is_peak].groupby("Date").sum()["FixLoad1"]
    return float(np.quantile(peak_elec, quantile))


def estimate_battery_discharge(elec_df: pd.DataFrame, quantile: float = 1.0) -> float:
    """
    Estimate the required battery discharging rate for a given electrical demand.

    This will try to set the discharge rate to the `quantile`th highest electrical demand experienced.
    A quantile of 1 will have the battery cover the highest electrical draw, and lower quantiles will
    estimate for a battery that is sometimes augmented by the grid.

    Parameters
    ----------
    elec_df
        EPOCH-friendly dataframe with "Date", "Start Time", and "FixLoad1" columns.
    quantile
        Ratio between 0 and 1 of the quantile to select. 0 is min (lowest discharge rate), 1 is max (highest discharge rate)

    Returns
    -------
    Estimated battery charging rate required in kW
    """
    elec_times = pd.to_datetime(elec_df["Date"] + " 2024 " + elec_df["Start Time"], utc=True)
    timedeltas = np.pad(
        [item.to_timedelta64() for item in np.ediff1d(elec_times)], pad_width=(0, 1), mode="wrap"
    ) / np.timedelta64(1, "h")
    return np.quantile(elec_df["FixLoad1"] / timedeltas, quantile)


def estimate_battery_charge(solar_df: pd.DataFrame, solar_scale: float = 1.0, quantile: float = 0.9) -> float:
    """
    Estimate the required battery charging rate for a given solar installation.

    This will try to set the charging rate to the solar power output on the `quantile`% best day
    (if `quantile == 1` then the maximum solar power generated).
    This approach tends to overestimate, and you might want to drop `quantile` and allow some grid export
    or energy usage.

    Parameters
    ----------
    solar_df
        EPOCH-friendly dataframe with "Date", "Start Time", and "RGen1" columns.
    solar_scale
        kWp rating of the solar PV installation (maybe from `estimate_solar_pv`)
    quantile
        Ratio between 0 and 1 of the quantile to select. 0 is min (lowest charge rate), 1 is max (highest charge rate)

    Returns
    -------
    Estimated battery charging rate required in kW
    """
    solar_output = solar_df["RGen1"].to_numpy() * solar_scale
    solar_times = pd.to_datetime(solar_df["Date"] + " 2024 " + solar_df["Start Time"], utc=True)
    # Convert from kWh / timestep into kW (e.g. something that uses 1kWh in 0.5 hours is a 2kW charge)
    timedeltas = np.pad(
        [item.to_timedelta64() for item in np.ediff1d(solar_times)], pad_width=(0, 1), mode="wrap"
    ) / np.timedelta64(1, "h")
    return np.quantile(solar_output / timedeltas, quantile)


def round_to_search_space(x: float, start: float, stop: float, step: float) -> float:
    """
    Round a given entry to the closest entry in the search space.

    This will clip if x < start or x > stop
    Parameters
    ----------
    x
        Parameter to get into the search space
    start
        Lowest value in the search space
    stop
        Largest value in the search space
    step
        Step between closest values in the search space.

    Returns
    -------
    float
        x rounded in the form (start + i * step)
    """
    x = np.round((x - start) / step, 0)
    x = step * x + start
    return np.clip(x, start, stop)
