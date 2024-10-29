"""Specific Octopus Agile functions, including lookup tables for regional costs and the wholesale to agile mapping."""

import numpy as np
import pandas as pd

from ...models.import_tariffs import GSPEnum

DISTRIBUTION_REGION_FACTORS = {
    GSPEnum.A: 2.10,
    GSPEnum.B: 2.00,
    GSPEnum.C: 2.00,
    GSPEnum.D: 2.20,
    GSPEnum.E: 2.10,
    GSPEnum.F: 2.10,
    GSPEnum.G: 2.10,
    GSPEnum.H: 2.10,
    GSPEnum.J: 2.20,
    GSPEnum.K: 2.20,
    GSPEnum.L: 2.30,
    GSPEnum.M: 2.00,
    GSPEnum.N: 2.10,
    GSPEnum.P: 2.40,
}

PEAK_REGION_FACTORS = {
    GSPEnum.A: 13,
    GSPEnum.B: 14,
    GSPEnum.C: 12,
    GSPEnum.D: 13,
    GSPEnum.E: 12,
    GSPEnum.F: 12,
    GSPEnum.G: 12,
    GSPEnum.H: 12,
    GSPEnum.J: 12,
    GSPEnum.K: 12,
    GSPEnum.L: 11,
    GSPEnum.M: 13,
    GSPEnum.N: 13,
    GSPEnum.P: 12,
}


def wholesale_to_agile(
    wholesale_df: pd.DataFrame, distribution_factor: float = 2.0, peak_factor: float = 11, price_cap: float = 95
) -> pd.DataFrame:
    """
    Convert a set of wholesale electrical unit costs in p / kWh to an Octopus Agile Tariff.

    This uses the equation published on Octopus's blog here:
    https://octopus.energy/blog/agile-pricing-explained/
    THe distribution factors and peak factors for a given region are available in the dicts in this module.
    Note that this provides a cost without VAT, and the price cap applies pre-VAT as well.

    Parameters
    ----------
    wholesale_df
        Pandas dataframe with time series index and "cost" column in p / kWh
    distribution_factor
        Octopus's D factor which is multiplicative and probably around 2.0-2.2
    peak_factor
        Peak premium charged between 16:00 and 19:00, added on to the (D * cost)
    price_cap
        Pre-VAT price cap applied to the tariff costs (35p in 2023, 95p in 2024)

    Returns
    -------
    Pandas dataframe with "cost" column and datetime index, in p / kWh pre-VAT.
    """
    agile_df = pd.DataFrame(index=wholesale_df.index, data={"cost": wholesale_df["cost"]})
    agile_df["cost"] *= distribution_factor
    assert isinstance(agile_df.index, pd.DatetimeIndex)
    is_peak_mask = np.logical_and(agile_df.index.hour >= 16, agile_df.index.hour < 19)
    agile_df.loc[is_peak_mask, "cost"] += peak_factor
    agile_df["cost"] = np.minimum(agile_df["cost"], price_cap)
    return agile_df
