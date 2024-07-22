"""
Heat pump related code, including coefficient of performance and efficiency calculations.
"""

import numpy as np


def air_source_heat_pump_cop(delta_t: float) -> float:
    """
    Calculate an air source heat pump coefficient of performance from the When2Heat dataset.

    https://www.nature.com/articles/s41597-019-0199-y
    https://github.com/oruhnau/when2heat/blob/master/input/cop/cop_parameters.csv

    Parameters
    ----------
    delta_t
        Temperature difference between air (heat source) and output water (heat sink)

    Returns
    -------
        Coefficient of performance, ratio between electricity in and heat out.
    """
    delta_t = np.clip(delta_t, 15.0, 100.0)
    return 6.08 - 0.0941 * delta_t + 0.000464 * delta_t**2


def ground_source_heat_pump_cop(delta_t: float) -> float:
    """
    Calculate a ground source heat pump coefficient of performance from the When2Heat dataset.

    https://www.nature.com/articles/s41597-019-0199-y
    https://github.com/oruhnau/when2heat/blob/master/input/cop/cop_parameters.csv

    Parameters
    ----------
    delta_t
        Temperature difference between soil (heat source) and output water (heat sink)

    Returns
    -------
        Coefficient of performance, ratio between electricity in and heat out.
    """
    delta_t = np.clip(delta_t, 15.0, 100.0)
    return 1.029 - 0.2084 * delta_t + 0.001322 * delta_t**2


def water_source_heat_pump_cop(delta_t: float) -> float:
    """
    Calculate a water source heat pump coefficient of performance from the When2Heat dataset.

    https://www.nature.com/articles/s41597-019-0199-y
    https://github.com/oruhnau/when2heat/blob/master/input/cop/cop_parameters.csv

    Parameters
    ----------
    delta_t
        Temperature difference between input water (heat source) and output water (heat sink)

    Returns
    -------
        Coefficient of performance, ratio between electricity in and heat out.
    """
    delta_t = np.clip(delta_t, 15.0, 100.0)
    return 9.99 - 0.2049 * delta_t + 0.001249 * delta_t**2
