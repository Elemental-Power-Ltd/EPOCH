"""
Functions from the Standard Assessment Procedure (SAP) and Reduced Data SAP (RdSAP).

Guidance from BRE:
https://files.bregroup.com/SAP/SAP%2010.2%20-%2011-04-2023.pdf
https://files.bregroup.com/SAP/RdSAP10-dt13.02.2024.pdf

Older conventions:
https://files.bregroup.com/bre-co-uk-file-library-copy/filelibrary/accreditation/rdsap_conventions/v3/SAP2005_9-83_Appendix_S_March2010.pdf

"""

import datetime
from enum import StrEnum, auto

import numpy as np

from ..utils.bank_holidays import UKCountryEnum


class RatingBandEnum(StrEnum):
    """Building efficiency rating bands as used by SAP and RdSAP (earlier letters are better)."""

    A = auto()
    B = auto()
    C = auto()
    D = auto()
    E = auto()
    F = auto()
    G = auto()


class BuildingAgeBand(StrEnum):
    """Building age bands as used by SAP and RdSAP (larger letters are newer)."""

    A = auto()
    B = auto()
    C = auto()
    D = auto()
    E = auto()
    F = auto()
    G = auto()
    H = auto()
    I = auto()  # noqa: E741
    J = auto()
    K = auto()
    L = auto()
    M = auto()


class BuildingTypeEnum(StrEnum):
    """Types of domestic buildings as used by SAP and RdSAP."""

    Detached = auto()
    SemiDetached = auto()
    EndTerrace = auto()
    MidTerrace = auto()
    EnclosedMidTerrace = auto()
    EnclosedEndTerrace = auto()
    Flat = auto()
    Maisonette = auto()


def year_to_age_band(construction_date: datetime.datetime, nation: UKCountryEnum) -> BuildingAgeBand:
    """
    Get the age banding for a given site based on the year of its construction.

    These are given in SAP 10.2 Section 3 Table 1
    https://files.bregroup.com/SAP/RdSAP10-dt13.02.2024.pdf

    For Isle of Man, use UKCountryEnum.England.

    Age bands generally match updates to the building regulations, and are one year after
    the building regs changed in a given region.

    Parameters
    ----------
    construction_date
        Approximate year of construction of this building
    nation
        Which part of the UK the building is in

    Returns
    -------
    BuildingAgeBand
        A SAP Banding for the age of this building.
    """
    age_bands = {
        UKCountryEnum.England: [
            (1900, BuildingAgeBand.A),
            (1929, BuildingAgeBand.B),
            (1949, BuildingAgeBand.C),
            (1966, BuildingAgeBand.D),
            (1975, BuildingAgeBand.E),
            (1982, BuildingAgeBand.F),
            (1990, BuildingAgeBand.G),
            (1995, BuildingAgeBand.H),
            (2002, BuildingAgeBand.I),
            (2006, BuildingAgeBand.J),
            (2011, BuildingAgeBand.K),
            (2022, BuildingAgeBand.L),
            (3000, BuildingAgeBand.M),
        ],
        UKCountryEnum.Wales: [
            (1900, BuildingAgeBand.A),
            (1929, BuildingAgeBand.B),
            (1949, BuildingAgeBand.C),
            (1966, BuildingAgeBand.D),
            (1975, BuildingAgeBand.E),
            (1982, BuildingAgeBand.F),
            (1990, BuildingAgeBand.G),
            (1995, BuildingAgeBand.H),
            (2002, BuildingAgeBand.I),
            (2006, BuildingAgeBand.J),
            (2011, BuildingAgeBand.K),
            (2022, BuildingAgeBand.L),
            (3000, BuildingAgeBand.M),
        ],
        UKCountryEnum.Scotland: [
            (1919, BuildingAgeBand.A),
            (1929, BuildingAgeBand.B),
            (1949, BuildingAgeBand.C),
            (1964, BuildingAgeBand.D),
            (1975, BuildingAgeBand.E),
            (1983, BuildingAgeBand.F),
            (1991, BuildingAgeBand.G),
            (1998, BuildingAgeBand.H),
            (2002, BuildingAgeBand.I),
            (2007, BuildingAgeBand.J),
            (2011, BuildingAgeBand.K),
            (2023, BuildingAgeBand.L),
            (3000, BuildingAgeBand.M),
        ],
        UKCountryEnum.NorthernIreland: [
            (1919, BuildingAgeBand.A),
            (1929, BuildingAgeBand.B),
            (1949, BuildingAgeBand.C),
            (1973, BuildingAgeBand.D),
            (1977, BuildingAgeBand.E),
            (1985, BuildingAgeBand.F),
            (1991, BuildingAgeBand.G),
            (1999, BuildingAgeBand.H),
            (2006, BuildingAgeBand.I),
            # No J in Northern Ireland
            (2013, BuildingAgeBand.K),
            (2022, BuildingAgeBand.L),
            (3000, BuildingAgeBand.M),
        ],
    }

    for year, age_band in age_bands[nation]:
        if construction_date.year <= year:
            return age_band
    raise ValueError(f"Couldn't find age band for {construction_date} in {nation}")


def rating_to_band(sap_rating: int) -> RatingBandEnum:
    """
    Calculate a rating band (like you'd see on an EPC) for a given numerical rating.

    Numerical ratings are generally in the range 1-100 (but can be higher for net energy
    exporters!), and are either Energy Cost Rating (£) or Energy Intensity Ratings (CO2e).

    Parameters
    ----------
    sap_rating
        Either an Energy Cost Rating or an Energy Intensity Rating

    Returns
    -------
    SAP letter band corresponding to this numerical rating
    """
    if sap_rating >= 92:
        return RatingBandEnum.A

    if sap_rating >= 81:
        return RatingBandEnum.B

    if sap_rating >= 69:
        return RatingBandEnum.C

    if sap_rating >= 55:
        return RatingBandEnum.D

    if sap_rating >= 39:
        return RatingBandEnum.E

    if sap_rating >= 21:
        return RatingBandEnum.F

    if sap_rating >= 1:
        return RatingBandEnum.G
    raise ValueError(f"Sap rating {sap_rating} must be positive")


def sap_co2_emissions(gas_usage: float, elec_usage: float) -> float:
    """
    Calculate the SAP CO2 emissions factor.

    This emissions factor is used in the Energy Intensity Rating using
    a fixed set of CO2 factors that are updated yearly.

    Parameters
    ----------
    gas_usage
        kWh equivalent of natural gas consumed over the period
    elec_usage
        kWh of electricity used over the period

    Returns
    -------
    float
        kg CO2e over the period according to SAP factors.
    """
    # Note that these are different between SAP 10.2 and RdSAP!
    gas_co2_factor = 0.210
    elec_co2_factor = 0.136

    return gas_co2_factor * gas_usage + elec_co2_factor * elec_usage


def sap_energy_cost(gas_usage: float, elec_usage: float) -> float:
    """
    Calculate the SAP energy cost factor.

    This cost factor is used in the Energy Intensity Rating using
    a fixed set of pricess that are updated.

    Parameters
    ----------
    gas_usage
        kWh equivalent of natural gas consumed over the period
    elec_usage
        kWh of electricity used over the period

    Returns
    -------
    float
        £ over the period according to SAP factors.
    """
    # Note that these are different between SAP 10.2 and RdSAP!
    gas_cost_factor = 3.64
    elec_cost_factor = 16.49

    return gas_usage * gas_cost_factor + elec_usage * elec_cost_factor


def environmental_impact_rating(co2_emissions: float, total_floor_area: float) -> int:
    """
    Calculate an Environmental Impact Rating for this building.

    The Environmental Impact Rating is used in non-domestic EPCs as a measure of how energy
    efficient a building is to run.
    You should use the SAP carbon factors to calculate this, as actual
    fuels can vary significantly.
    SAP 10.2 Section 14
    https://files.bregroup.com/SAP/SAP%2010.2%20-%2011-04-2023.pdf

    The EI rating scale has been set so that EI 100 is achieved at zero net emissions.
    It can rise above 100 if the dwelling is a net exporter of energy.
    The EI rating is essentially independent of floor area.

    Parameters
    ----------
    co2_emissions
        SAP weighted CO2 emissions across a year across all fuels
    total_floor_area
        Total floor area in m^2

    Returns
    -------
    int
        Integer Environmental Impact rating
    """
    carbon_factor = co2_emissions / (total_floor_area + 45)

    if carbon_factor >= 28.3:
        ei_rating = 200 - 0.95 * np.log10(carbon_factor)
    else:
        ei_rating = 100 - 1.34 * carbon_factor

    return int(max(ei_rating, 1))


def energy_cost_rating(sap_energy_cost: float, total_floor_area: float) -> int:
    """
    Calculate an Energy Cost Rating for this building.

    The Energy Cost Rating is used in Domestic EPCs as a measure of how energy
    efficient a building is to run.
    You should use the SAP energy cost factors to calculate this, as actual
    tariffs can vary significantly.

    100 is the best rating, and net exporters can have a rating above 100.
    1 is the worst rating.

    SAP 10.2 Section 13
    https://files.bregroup.com/SAP/SAP%2010.2%20-%2011-04-2023.pdf

    Parameters
    ----------
    sap_energy_cost
        Total energy cost across all fuels as calculated by SAP methodology
    total_floor_area
        Floor area in m^2 of this building

    Returns
    -------
    int
        Integer SAP rating likely between 1 and 100
    """
    deflator = 0.36
    energy_cost_factor = deflator * sap_energy_cost / (total_floor_area + 45)

    if energy_cost_factor >= 3.5:
        ec_rating = 108.8 - 120.5 * np.log10(energy_cost_factor)
    else:
        ec_rating = 100 - 16.21 * energy_cost_factor

    return int(max(ec_rating, 1))


def estimate_interior_area(
    external_perimeter: float,
    external_area: float,
    wall_width: float = 0.25,
    building_type: BuildingTypeEnum = BuildingTypeEnum.Detached,
) -> float:
    """
    Estimate the interior floor area of a building given an exterior perimeter and area rating.

    You can probably get these numbers from satellite views, e.g. measurements on Google Maps.
    In the simplest case, the interior area is just the exterior area minus some contribution of the walls.
    For some types of buildings, however, the calculation is more complex and is derived from
    RdSAP 10 Section 4.4 Table 2
    https://files.bregroup.com/SAP/RdSAP10-dt13.02.2024.pdf

    Parameters
    ----------
    external_perimeter
        External perimeter of this building in m
    external_area
        Externally measured area of this building in m^2
    wall_width
        Weighted average width of the walls in this building in m
    building_type
        What sort of building this is

    Returns
    -------
    float
        Interior area in m^2
    """
    if building_type == BuildingTypeEnum.Detached:
        internal_perimeter = external_perimeter - 8.0 * wall_width
        return external_area - wall_width * internal_perimeter - wall_width**2

    if building_type in {BuildingTypeEnum.SemiDetached, BuildingTypeEnum.EndTerrace}:
        if external_perimeter**2 > 8.0 * external_area:
            internal_perimeter = external_perimeter - 8.0 * wall_width
            a = 0.5 * (external_perimeter - np.sqrt(external_perimeter**2 - 8 * external_area))
            return float(external_area - wall_width * (external_perimeter + 0.5 * a) + 3 * wall_width**2)
        return external_area - (wall_width * external_perimeter) + (3 * wall_width**2)

    if building_type == BuildingTypeEnum.MidTerrace:
        return external_area - wall_width * (external_perimeter + 2 * external_area / external_perimeter) + 2 * wall_width**2

    if building_type == BuildingTypeEnum.EnclosedEndTerrace:
        return external_area - (1.5 * wall_width * external_perimeter) + 2.25 * wall_width**2

    if building_type == BuildingTypeEnum.EnclosedMidTerrace:
        return (
            external_area - wall_width * ((external_area / external_perimeter) + 1.5 * external_perimeter) + 1.5 * wall_width**2
        )

    raise ValueError(f"Got invalid building type {building_type}")


def estimate_window_area(
    total_floor_area: float,
    building_type: BuildingTypeEnum = BuildingTypeEnum.Detached,
    building_age_band: BuildingAgeBand = BuildingAgeBand.A,
) -> float:
    """
    Estimate the window area given floor area, building type, and age band.

    This isn't a great method, and is adapted from the RdSAP 2005 Conventions note.
    https://files.bregroup.com/bre-co-uk-file-library-copy/filelibrary/accreditation/rdsap_conventions/v3/SAP2005_9-83_Appendix_S_March2010.pdf

    It was removed from future SAP versions due to inaccuracy, but will give an initial guess
    for other fitting routines if necessary.

    Parameters
    ----------
    total_floor_area
        Total interior floor area across all stories in this building, in m^2
    building_type
        The closest matching domestic building type for this site (e.g. Flat or Detached)
    building_age_band
        The age band representing when this building was constructed (according to the SAP 2005 rules)

    Returns
    -------
    float
        Estimated window area in m^2
    """

    def estimate_window_area_flat(total_floor_area: float, building_age_band: BuildingAgeBand) -> float:
        """Estimate the window area for a flat or maisonette given floor area, building type, and age band."""
        if building_age_band in {BuildingAgeBand.A, BuildingAgeBand.B, BuildingAgeBand.C}:
            return 0.0801 * total_floor_area + 5.580
        if building_age_band == BuildingAgeBand.D:
            return 0.0341 * total_floor_area + 8.562
        if building_age_band == BuildingAgeBand.E:
            return 0.0717 * total_floor_area + 6.560
        if building_age_band == BuildingAgeBand.F:
            return 0.1199 * total_floor_area + 1.975
        if building_age_band == BuildingAgeBand.G:
            return 0.0501 * total_floor_area + 4.554
        if building_age_band == BuildingAgeBand.H:
            return 0.0813 * total_floor_area + 3.744
        if building_age_band >= BuildingAgeBand.I:
            return 0.1148 * total_floor_area + 0.392
        raise ValueError(f"Invalid building age band for window size estimation {building_age_band}")

    def estimate_window_area_detached(total_floor_area: float, building_age_band: BuildingAgeBand) -> float:
        """Estimate the window area for a building given floor area, building type, and age band."""
        if building_age_band in {BuildingAgeBand.A, BuildingAgeBand.B, BuildingAgeBand.C}:
            return 0.1220 * total_floor_area + 6.875
        if building_age_band == BuildingAgeBand.D:
            return 0.1294 * total_floor_area + 5.515
        if building_age_band == BuildingAgeBand.E:
            return 0.1239 * total_floor_area + 7.332
        if building_age_band == BuildingAgeBand.F:
            return 0.1252 * total_floor_area + 5.520
        if building_age_band == BuildingAgeBand.G:
            return 0.1356 * total_floor_area + 5.252
        if building_age_band == BuildingAgeBand.H:
            return 0.0948 * total_floor_area + 6.534
        if building_age_band == BuildingAgeBand.I:
            return 0.1382 * total_floor_area - 0.027
        if building_age_band >= BuildingAgeBand.J:
            return 0.1435 * total_floor_area + 0.403
        raise ValueError(f"Invalid building age band for window size estimation {building_age_band}")

    if building_type in {BuildingTypeEnum.Flat, BuildingTypeEnum.Maisonette}:
        return estimate_window_area_flat(total_floor_area, building_age_band)

    return estimate_window_area_detached(total_floor_area, building_age_band)
