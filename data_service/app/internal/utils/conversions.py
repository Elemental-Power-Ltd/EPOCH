"""
Conversion functions between certain units and measures.

Functions of the form
```
def celsius_to_fahreinheit(temp_c: float) -> float:
    return (temp_c * 9.0 / 5.0) + 32
```
belong in here.

Where possible, these functions should work equally well on numpy arrays or on single float values.
"""

import numpy as np

from ..epl_typing import FloatOrArray


def m3_to_kwh(vol: FloatOrArray, calorific_value: float = 38.0) -> FloatOrArray:
    """
    Convert a gas reading in meters cubed to kWh.

    Parameters
    ----------
    vol
        Volume of gas consumed
    calorific_value
        Energy per unit gas in MJ. Provided on bill.

    Returns
    -------
    gas energy consumption in kWh
    """
    return vol * calorific_value * 1.02264 / 3.6


def celsius_to_kelvin(temperature: FloatOrArray) -> FloatOrArray:
    """
    Convert a temperature in Celsius to one in Kelvin.

    This checks that you haven't already converted it, and that it's a reasonable air temperature.

    Parameters
    ----------
    temperature
        Air temperature in celsius between -50°C and 100°C

    Returns
    -------
        Temperature in Kelvin between 223.15K and 373.15K
    """
    if isinstance(temperature, float | int):
        assert -50 <= temperature < 100, (
            f"{temperature} out of range of likely °C values [-50, 100). Have you already converted it?"
        )
    else:
        assert np.all(np.logical_and(-50 <= temperature, temperature < 100)), (
            f"{temperature} out of range of likely °C values [-50, 100). Have you already converted it?"
        )
    return temperature + 273.15


def millibar_to_megapascal(pressure: FloatOrArray) -> FloatOrArray:
    """
    Convert an air pressure in mbar into one in MPa.

    VisualCrossing provides us with air temperatures in mbar, but
    for some equations we want it in megapascals.
    This checks that you haven't already converted it, and that it's
    a reasonable air pressure (outside this range is very bad news).

    Parameters
    ----------
    pressure
        Air pressure in mbar between 800 and 1100 mbar

    Returns
    -------
        air pressure in MPa between 0.08 and 0.11 MPa
    """
    if isinstance(pressure, float | int):
        assert 800 < pressure < 1100, (
            f"{pressure} out of range of likely mbar values [800, 1100). Have you already converted it?"
        )
    else:
        assert np.all(np.logical_and(800 < pressure, pressure < 1100)), (
            f"{pressure} out of range of likely mbar values [800, 1100). Have you already converted it?"
        )
    return pressure / 10000


def relative_to_specific_humidity(rel_hum: FloatOrArray, air_temp: FloatOrArray, air_pressure: FloatOrArray) -> FloatOrArray:
    """
    Convert a relative (%) humidity to a specific humidity in grams of water per kg of air.

    Involves a lot of awful empirical formulae and fitted equations.
    Mostly extracted from
    https://www.aqua-calc.com/calculate/humidity
    which cites
    https://doi.org/10.1063/1.1461829 p 398-399

    Parameters
    ----------
    relative_humidity
        Relative humidity in range [0, 100)
    air_temp
        Air temperature in range [-50, 100) in °C
    air_pressure
        Air pressure in range [900, 1100] in mbar

    Returns
    -------
        mixing ratio in grams of water per kg of air
    """
    if isinstance(rel_hum, float | int):
        assert 0 <= rel_hum <= 100, f"Relative humidity must be in range [0, 100]. Got {rel_hum}"
    else:
        bad_mask = ~np.logical_and(0.0 <= rel_hum, rel_hum <= 100.0)
        assert np.all(np.logical_and(0.0 <= rel_hum, rel_hum <= 100.0)), (
            f"All relative humidities must be in range [0, 100]. Got {rel_hum[bad_mask]}."
        )

    if isinstance(air_temp, float | int):
        assert -50 <= air_temp < 100, f"{air_temp} out of range of likely °C values [-50, 100). Have you already converted it?"
    else:
        assert np.all(np.logical_and(-50.0 <= air_temp, air_temp < 100.0)), (
            f"{air_temp} out of range of likely °C values [-50, 100). Have you already converted it?"
        )

    if isinstance(air_pressure, float | int):
        assert 900 <= air_pressure < 1100, "air pressure must be in the range [900, 1100)"
    else:
        assert np.all(np.logical_and(900 <= air_pressure, air_pressure < 1100.0)), (
            f"{air_pressure} out of range of likely values [900, 1100). Is it in the right units?"
        )

    def enhancement_factor(temperature: FloatOrArray, pressure: FloatOrArray) -> FloatOrArray:
        """
        Corrections for vapour pressures for moist air.

        The Buck equation is for pure water, and not just moist air.
        We "enhance" it by a small factor, which is fitted empirically here.

        New Equations for Computing Vapor Pressure and Enhancement Factor
        Arden L. Buck
        https://doi.org/10.1175/1520-0450(1981)020<1527:NEFCVP>2.0.CO;2

        Parameters
        ----------
        temperature
            Temperature in Celsius
        pressure
            Pressure in mbar

        Returns
        -------
            enhancement factor in range [1.0, 1.005]ish
        """
        A, B, C, D, E = 4.1e-4, 3.48e-6, 7.4e-10, 30.6, -3.8e-2
        return 1.0 + A + pressure * (B + C * (temperature + D + E * pressure) ** 2)

    air_pres_pa: FloatOrArray = millibar_to_megapascal(air_pressure) * 1e6
    vap_pres_at_t_ref = 611.21  # Pa
    # vapour pressure at 0C via
    # CRC Handbook of Chemistry and Physics, 85th Edition, Volume 85
    # https://books.google.co.uk/books?id=WDll8hA006AC&pg=SA6-PA10&redir_esc=y#v=onepage&q&f=false

    # Calculate the equilibrium mixing ratio via the Buck equation
    eqm_mixing_ratio: FloatOrArray = vap_pres_at_t_ref * np.exp(
        (18.678 - (air_temp / 234.5)) * (air_temp / (air_temp + 257.14))
    )  # type: ignore

    eqm_mixing_ratio *= enhancement_factor(air_temp, air_pressure)
    # Ratio of molar specific gas constants for water (molar mass 18 g mol^-1) to dry air (avg molar mass ~29 g mol^-1)
    gas_constant_ratio = 18 / 28.964917

    g_per_kg = 1e3
    return g_per_kg * (rel_hum / 100) * gas_constant_ratio * eqm_mixing_ratio / air_pres_pa
