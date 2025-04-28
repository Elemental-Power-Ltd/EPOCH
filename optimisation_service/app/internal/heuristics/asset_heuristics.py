"""
Asset heuristics for initialising EPOCH search spaces.
"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd


class HeatPump:
    @staticmethod
    def heat_power(
        building_hload: list[float],
        ashp_input_table: list[list[float]],
        ashp_output_table: list[list[float]],
        air_temperature: list[float],
        timestamps: list[datetime],
        ashp_mode: float,
        quantile: float = 0.99,
    ) -> float:
        """
        Estimate the air source heat pump electrical power rating.

        This will attempt to size a heat pump considering COP to meet the x% highest heat demand of the year.
        The electrical load is (heat load / cop) at each timestep in kW.
        Generally heat loads are sized for the 99th percentile, i.e. the heat pump must provide adequate heat on the 1% coldest
        day of the year.

        Parameters
        ----------
        building_hload
            List of heat loads.
        ashp_input_table
            Air source heat pump power draw table in a row major list.
        ashp_output_table
            Air source heat pump heat output in a row major list.
        air_temperature
            List of air temperatures in °C.
        timestamps
            List of datetimes corresponding to the building_hload.
        ashp_mode
            Air source heat pump mode matching the column headers of the ASHP dataframes, this is either a weather compensation
            setting or a flow temperature.
        quantile
            Percentile worst head load to size for

        Returns
        -------
        Estimated heat pump electrical rating in kW
        """
        ashp_input_arr = np.array(ashp_input_table)
        ashp_output_arr = np.array(ashp_output_table)

        ashp_input_row = ashp_input_arr[1:, ashp_input_arr[0, :] == ashp_mode].flatten()
        ashp_output_row = ashp_output_arr[1:, ashp_output_arr[0, :] == ashp_mode].flatten()

        ashp_inputs = np.interp(air_temperature, ashp_input_arr[1:, 0], ashp_input_row)
        ashp_outputs = np.interp(air_temperature, ashp_output_arr[1:, 0], ashp_output_row)

        cops = ashp_outputs / ashp_inputs

        timedeltas = np.pad(np.diff(np.array(timestamps)), pad_width=(0, 1), mode="wrap") / timedelta(hours=1)

        elec_loads = (np.array(building_hload) / cops) / timedeltas
        return np.quantile(elec_loads, quantile)


class Renewables:
    @staticmethod
    def yield_scalars(solar_yield: list[float], building_eload: list[float], quantile: float = 0.75) -> float:
        """
        Estimate the solar PV array size for this site to cover a fraction of daily usage.

        This will size the RGen1 array to cover all electrical demand at x% of sunny timesteps, where x% is chosen by
        `quantile`.
        A sunny timestep has non-zero solar generation, but this can be very low (e.g. clear winter evenings).
        If quantile is set large this will significantly oversize the solar array as it attempts to cover all electrical usage.
        If quantile is small, the solar array will be closer to being sized for summer afternoons.

        Parameters
        ----------
        solar_yield
            List of potential solar outputs of a 1kWp array on this site.
        building_eload
            List of electrical load values.
        quantile
            What fraction of electrical loads during sunny days to attempt to cover

        Returns
        -------
        Estimated solar array size in kWp
        """
        is_nonzero_solar = np.array(solar_yield) > 0
        required_solar = np.array(building_eload)[is_nonzero_solar] / np.array(solar_yield)[is_nonzero_solar]
        return float(np.quantile(required_solar, quantile))


class EnergyStorageSystem:
    @staticmethod
    def capacity(building_eload: list[float], timestamps: list[datetime], quantile: float = 0.75) -> float:
        """
        Estimate the required battery capacity to avoid peak time usage.

        This will select a battery size to cover the `quantile`% worst 16:00-19:00 period.
        Set `quantile` to 1 to cover the maximally bad 16:00-19:00 period.

        Parameters
        ----------
        building_eload
            List of electrical load values.
        timestamps
            List of datetimes corresponding to the building_eload.
        quantile
            What fraction of days 16:00-19:00 period we should cover.

        Returns
        -------
        Estimated battery capacity for this site in kWh
        """
        time_of_day = np.array([dt.hour for dt in timestamps])
        is_peak = np.logical_and(time_of_day >= 16, time_of_day < 19)
        elec_df = pd.DataFrame({"load": building_eload, "Date": time_of_day})
        peak_elec = elec_df[is_peak].groupby("Date").sum()["load"]

        return float(np.quantile(peak_elec, quantile))

    @staticmethod
    def discharge_power(building_eload: list[float], timestamps: list[datetime], quantile: float = 1.0) -> float:
        """
        Estimate the required battery discharging rate for a given electrical demand.

        This will try to set the discharge rate to the `quantile`th highest electrical demand experienced.
        A quantile of 1 will have the battery cover the highest electrical draw, and lower quantiles will
        estimate for a battery that is sometimes augmented by the grid.

        Parameters
        ----------
        building_eload
            List of electrical load values.
        timestamps
            List of datetimes corresponding to the building_eload.
        quantile
            Ratio between 0 and 1 of the quantile to select. 0 is min (lowest discharge rate), 1 is max (highest discharge rate)

        Returns
        -------
        Estimated battery charging rate required in kW
        """
        timedeltas = np.pad(np.diff(np.array(timestamps)), pad_width=(0, 1), mode="wrap") / timedelta(hours=1)
        return np.quantile(np.array(building_eload) / timedeltas, quantile)

    @staticmethod
    def charge_power(
        solar_yield: list[float], timestamps: list[datetime], solar_scale: float = 1.0, quantile: float = 0.9
    ) -> float:
        """
        Estimate the required battery charging rate for a given solar installation.

        This will try to set the charging rate to the solar power output on the `quantile`% best day
        (if `quantile == 1` then the maximum solar power generated).
        This approach tends to overestimate, and you might want to drop `quantile` and allow some grid export
        or energy usage.

        Parameters
        ----------
        solar_yield
            List of potential solar outputs of a 1kWp array on this site.
        timestamps
            List of datetimes corresponding to the solar_yield.
        solar_scale
            kWp rating of the solar PV installation (maybe from `estimate_solar_pv`)
        quantile
            Ratio between 0 and 1 of the quantile to select. 0 is min (lowest charge rate), 1 is max (highest charge rate)

        Returns
        -------
        Estimated battery charging rate required in kW
        """
        solar_output = np.array(solar_yield) * solar_scale
        # Convert from kWh / timestep into kW (e.g. something that uses 1kWh in 0.5 hours is a 2kW charge)
        timedeltas = np.pad(np.diff(np.array(timestamps)), pad_width=(0, 1), mode="wrap") / timedelta(hours=1)
        return np.quantile(solar_output / timedeltas, quantile)
