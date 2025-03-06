"""
Models for energy performance certificates and display energy certificates.

Source JSON schemas available here:
https://epc.opendatacommunities.org/docs/csvw
"""

# ruff: noqa: D101
from enum import IntEnum, StrEnum

import pydantic


class CertificateType(StrEnum):
    NonDomesticEPC = "NonDomesticEPC"
    NonDomesticDEC = "NonDomesticDEC"
    DomesticEPC = "DomesticEPC"
    AirConditioning = "AirConditioning"


class AcInspectionCommissionedEnum(IntEnum):
    InspectionCompleted = 1
    InspectionCommissioned = 2
    NoInspection = 3
    NotRelevant = 4
    DontKnow = 5


class UprnSourceEnum(StrEnum):
    AddressMatched = "Address Matched"
    EnergyAssessor = "Energy Assessor"


class ImpactEnum(StrEnum):
    Low = "low"
    Medium = "medium"
    High = "high"


class EpcPaybackEnum(StrEnum):
    Short = "short"
    Medium = "medium"
    Long = "long"
    Other = "other"


class NonDomesticRecommendation(pydantic.BaseModel):
    # We get fields in kebab-case from the EPC API, so
    # generate snake_case aliases for each of them
    model_config = pydantic.ConfigDict(
        alias_generator=pydantic.AliasGenerator(
            validation_alias=lambda field_name: field_name.replace("_", "-"),
        ),
        str_strip_whitespace=True,
    )
    lmk_key: str = pydantic.Field(
        description=(
            "Individual lodgement identifier."
            "Guaranteed to be unique and can be used to identify a certificate in the downloads and the API."
        ),
        max_length=64,
    )
    recommendation_item: int = pydantic.Field(description="Used to order the recommendations on the output EPC.")
    recommendation_code: str = pydantic.Field(description="Shorthand code to represent the recommendation.")
    recommendation: str = pydantic.Field(description="Description of the suggested improvement.")
    co2_impact: ImpactEnum = pydantic.Field(
        description="Categorical descriptor defining the impact on CO₂ emissions (e.g. LOW)."
    )
    payback_type: EpcPaybackEnum

    @pydantic.field_validator("payback_type", mode="before")
    @classmethod
    def payback_type_lower(cls, v: str) -> EpcPaybackEnum:
        """Strip and lower the payback string, as it can be inconsistent."""
        return EpcPaybackEnum(v.strip().lower())

    @pydantic.field_validator("co2_impact", mode="before")
    @classmethod
    def impact_type_lower(cls, v: str) -> ImpactEnum:
        """Strip and lower the impact string, as it can be inconsistent."""
        return ImpactEnum(v.strip().lower())


class NonDomesticEPCBase(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        alias_generator=pydantic.AliasGenerator(
            validation_alias=lambda field_name: field_name.replace("_", "-"),
        ),
        str_strip_whitespace=True,
    )

    ac_inspection_commissioned: AcInspectionCommissionedEnum | None = pydantic.Field(
        description=(
            "One of:1=Yes, inspection completed; 2=Yes, inspection commissioned;"
            " 3=No inspection completed or commissioned; 4=Not relevant; 5=Don't know"
        )
    )
    address: str = pydantic.Field(
        description=(
            "Field containing the concatenation of address1, address2 and address3. Note that post code is recorded separately."
        )
    )
    aircon_kw_rating: float | None = pydantic.Field(description="Air conditioning System. Rating in kW")
    aircon_present: bool | None = pydantic.Field(
        description="Air Conditioning System. Does the building have an air conditioning system?"
    )
    building_environment: str = pydantic.Field(
        description=(
            "Building environment which is taken as the servicing strategy that contributes the largest proportion "
            " of the building's CO2 emissions."
        )
    )
    constituency: str = pydantic.Field(
        description="Office for National Statistics (ONS) code. Parliamentary constituency in which the building is located."
    )
    constituency_label: str = pydantic.Field(
        description=(
            "The name of the parliamentary constituency in which the building is located."
            " This field is for additional information only and should not be relied upon:"
            " please refer to the Constituency ONS Code."
        )
    )
    county: str = pydantic.Field(description="County in which the building is located (where applicable)")
    estimated_aircon_kw_rating: float | None = pydantic.Field(
        description=(
            "Air Conditioning System."
            "If exact rating unknown, what is the estimated total effective output rating of the air conditioning system in kW."
        )
    )
    floor_area: float = pydantic.Field(  # type: ignore
        description=(
            "The total useful floor area is the total of all enclosed spaces measured to the internal face"
            " of the external walls, i.e. the gross floor area as measured in accordance with the guidance issued from"
            " time to time by the Royal Institute of Chartered Surveyors or by a body replacing that institution. (m2)"
        ),
        alias=pydantic.AliasChoices("floor_area", "total_floor_area", "floor-area", "total-floor-area"),  # type: ignore
    )
    inspection_date: pydantic.types.NaiveDatetime = pydantic.Field(
        description="The date that the inspection was actually carried out by the energy assessor"
    )
    lmk_key: str
    local_authority: str = pydantic.Field(
        description="Office for National Statistics (ONS) code. Local authority area in which the building is located."
    )
    local_authority_label: str = pydantic.Field(
        description=(
            "The name of the local authority area in which the building is located."
            " This field is for additional information only and should not be relied upon:"
            " please refer to the Local Authority ONS Code."
        )
    )
    lodgement_date: pydantic.types.NaiveDatetime = pydantic.Field(
        description="Date lodged on the Energy Performance of Buildings Register"
    )
    lodgement_datetime: pydantic.types.NaiveDatetime = pydantic.Field(
        description="Date and time lodged on the Energy Performance of Buildings Register."
    )
    main_heating_fuel: str = pydantic.Field(
        max_length=37,
        description=(
            "Main Heating fuel for the building is taken as the fuel which delivers"
            " the greatest total thermal output for space or water heating."
        ),
    )
    other_fuel_desc: str | None = pydantic.Field(  # type: ignore
        description="Text description of unspecified fuel type if 'Other' is selected for Main Heating Fuel.",
        alias=pydantic.AliasChoices("other_fuel", "other_fuel_desc", "other-fuel", "other-fuel-desc"),  # type: ignore
    )
    posttown: str = pydantic.Field(description="Post town for the building address.")
    primary_energy: float | None = pydantic.Field(
        description="Displayed on the non-domestic EPC as primary energy use (kWh/m2 per year)", default=None
    )
    property_type: str = pydantic.Field(description="Describes the type of building that is being inspected.")
    recommendations: list[NonDomesticRecommendation] | None = pydantic.Field(
        description="List of recommendations for this site", default=None
    )
    uprn: int | None = pydantic.Field(
        description="The UPRN submitted by an assessor or alternatively from the department's address matching algorithm."
    )
    uprn_source: UprnSourceEnum | None = pydantic.Field(
        description="Populated with the values 'Energy Assessor' or 'Address Matched' to show how the UPRN was populated."
    )
    renewable_sources: str | None = pydantic.Field(
        description="On-site renewable energy sources. This only appears on the Advisory Report."
    )

    @pydantic.field_validator(
        "address1",
        "address2",
        "address3",
        "constituency",
        "other_fuel_desc",
        "special_energy_uses",
        "renewable_sources",
        "uprn",
        mode="before",
        check_fields=False,
    )
    def remove_blank_strings(cls, v: str | None) -> str | None:
        """Remove whitespace from EPC and return None if empty."""
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        return v

    @pydantic.field_validator("aircon_kw_rating", "estimated_aircon_kw_rating", mode="before")
    def remove_blank_floats(cls, v: str | float) -> float | None:
        """Remove whitespace from floats and return None if empty."""
        if isinstance(v, float):
            return v
        v = v.strip()
        if not v:
            return None
        return float(v)

    @pydantic.field_validator("ac_inspection_commissioned", mode="before")
    def remove_blank_int(cls, v: str | int) -> int | None:
        """Remove whitespace from integers and return None if empty."""
        if isinstance(v, int):
            return v
        v = v.strip()
        if not v:
            return None
        return int(float(v))

    @pydantic.field_validator("uprn_source", mode="before")
    def remove_blank_uprn_source(cls, v: str) -> UprnSourceEnum | None:
        """Remove whitespace from UPRN sources and return None if empty."""
        v = v.strip()
        if not v:
            return None
        return UprnSourceEnum(v)

    @pydantic.field_validator("aircon_present", mode="before")
    def remove_blank_bool(cls, v: str) -> str | None:
        """Remove whitespace from bools and return None if empty."""
        v = v.strip()
        if not v:
            return None
        return v


class NonDomesticDEC(NonDomesticEPCBase):
    current_operational_rating: float | None = pydantic.Field(
        description=(
            "Current Operational Rating (OR) for this building."
            " A numeric indicator of the amount of energy consumed during the occupation of the building over a period of"
            " 12 months. An OR is a measure of the annual (CO₂) emission per unit of area of the building caused by its"
            " consumption of energy, compared to a value that would be considered typical for the particular type of building."
            " The numbers do not represent actual units of energy consumed; they represent comparative energy efficiency."
        )
    )
    yr1_operational_rating: float | None = pydantic.Field(description="Operational Ratings from previous years (CO₂).")
    yr2_operational_rating: float | None = pydantic.Field(description="Operational Ratings from previous years (CO₂).")
    operational_rating_band: str = pydantic.Field(
        max_length=8,
        description=(
            "Current Operational Rating converted into an energy band/grade into a linear 'A to G' scale"
            " (where A is the most energy efficient and G the least energy efficient)."
        ),
    )
    electric_co2: float | None = pydantic.Field(
        description=(
            "Total CO₂ emissions from electricity. The energy used by the building is converted into an"
            " amount of carbon dioxide (CO₂). Different types of fuel emit different amounts of CO₂."
            " Total CO₂ emissions in tonnes per year of CO₂."
        )
    )
    heating_co2: float | None = pydantic.Field(
        description=(
            "Total CO₂ emissions from heating."
            " The energy used by the building is converted into an amount of carbon dioxide (CO₂)."
            " Different types of fuel emit different amounts of CO₂. Total CO₂ emissions in tonnes per year of CO₂."
        )
    )
    renewables_co2: float | None = pydantic.Field(
        description=(
            "Total CO₂ emissions from Renewable sources."
            " On-Site Renewables (OSR) include technologies that generate heat or electricity from ambient sources"
            " and have zero (or near zero) CO₂ emissions."
            " The energy they deliver reduces CO₂ emissions from the building."
        )
    )
    main_benchmark: str = pydantic.Field(
        max_length=39,
        description=(
            "The benchmark is the average energy performance for a building of this type,"
            " under a number of standardised conditions for temperature, occupancy and proportion of"
            " non-electrical energy used. Under certain circumstances, these benchmarks may be adjusted"
            " according to location, occupancy and the ratio of non-electrical energy used."
        ),
    )
    special_energy_uses: str | None = pydantic.Field(
        max_length=248,
        default=None,
        description=(
            "Separable energy uses. The aim of the Operational Rating is to compare the annual energy"
            " consumption of the building with that of a building typical of its type. In some cases"
            " the building may include activities that consume energy and which are not considered typical"
            " of that building type. It may be reasonable to subtract these separable energy uses in"
            " certain circumstances. In order to be able to isolate and remove the annual separable energy"
            " consumption from the total, any separable energy uses must be separately metered."
            " This only appears on the Recommendations Report."
        ),
    )
    annual_thermal_fuel_usage: float | None = pydantic.Field(description="Annual Energy Use (kWh/m²/year) for heating")
    typical_thermal_fuel_usage: float | None = pydantic.Field(description="Typical Energy Use (kWh/m²/year) for heating")
    annual_electrical_fuel_usage: float | None = pydantic.Field(description="Annual Energy Use (kWh/m²/year) for electricity")
    typical_electric_fuel_usage: float | None = pydantic.Field(
        description="Typical Energy Use (kWh/m²/year) for electricity", default=None
    )
    renewables_fuel_thermal: float | None = pydantic.Field(
        description="Percentage of energy obtained from on-site renewable sources for heating (if any)"
    )
    renewables_electrical: float | None = pydantic.Field(
        description="Percentage of energy obtained from on-site renewable sources for electricity (if any)."
    )
    yr1_electricity_co2: float | None = pydantic.Field(
        description=(
            "CO₂ emissions from electricity in previous reporting year (if any). Total CO₂ emissions in tonnes per year of CO₂."
        )
    )
    yr2_electricity_co2: float | None = pydantic.Field(
        description=(
            "CO₂ emissions from electricity in previous reporting year (if any). Total CO₂ emissions in tonnes per year of CO₂."
        )
    )
    yr1_heating_co2: float | None = pydantic.Field(
        description=(
            "CO₂ emissions from heating in previous reporting year (if any). Total CO₂ emissions in tonnes per year of CO₂."
        )
    )
    yr2_heating_co2: float | None = pydantic.Field(
        description=(
            "CO₂ emissions from heating in previous reporting year (if any). Total CO₂ emissions in tonnes per year of CO₂."
        )
    )
    yr1_renewables_co2: float | None = pydantic.Field(
        description=(
            "CO₂ emissions from renewable sources in previous reporting year (if any)."
            " Total CO₂ emissions in tonnes per year of CO₂."
        )
    )
    yr2_renewables_co2: float | None = pydantic.Field(
        description=(
            "CO₂ emissions from renewable sources in previous reporting year (if any)."
            " Total CO₂ emissions in tonnes per year of CO₂."
        )
    )
    building_category: str = pydantic.Field(
        max_length=275,
        description=(
            "Building category codes (described below). This data field may contain multiple benchmark categories."
            " Where a building has a mix of uses that would place parts of the building in a different benchmark category,"
            " it is possible to construct a composite benchmark, e.g. a school with a swimming pool."
        ),
    )
    nominated_date: pydantic.NaiveDatetime = pydantic.Field(
        description=(
            "The default nominated date is the assessment date."
            " The assessor can select an alternative nominated date no later than three months"
            " after the end of the assessment period."
        )
    )
    or_assessment_end_date: pydantic.NaiveDatetime = pydantic.Field(description="Specified end date of the assessment period.")
    occupancy_level: str = pydantic.Field(max_length=18, description="Occupancy during the hours of operation of the building.")

    @pydantic.field_validator(
        "yr1_electricity_co2",
        "yr2_electricity_co2",
        "yr1_heating_co2",
        "yr2_heating_co2",
        "yr1_renewables_co2",
        "yr2_renewables_co2",
        "current_operational_rating",
        "yr1_operational_rating",
        "yr2_operational_rating",
        "electric_co2",
        "heating_co2",
        "renewables_co2",
        "annual_thermal_fuel_usage",
        "typical_thermal_fuel_usage",
        "annual_electrical_fuel_usage",
        "renewables_fuel_thermal",
        "renewables_electrical",
        mode="before",
    )
    def remove_blank_floats_dec(cls, v: str | float) -> float | None:
        """Remove whitespace from floats and return None if empty."""
        if isinstance(v, float):
            return v
        v = v.strip()
        if not v:
            return None
        return float(v)


class NonDomesticEPC(NonDomesticEPCBase):
    asset_rating: int | None = pydantic.Field(
        description=(
            "Energy Performance Asset Rating. The CO₂ emissions from the actual building in comparison"
            " to a Standard Emission Rate. (kg CO₂/m²)"
        ),
        default=None,
    )
    asset_rating_band: str | None = pydantic.Field(
        default=None,
        description=(
            "Energy Performance Asset Rating converted into an energy band/grade into a linear"
            " 'A+ to G' scale (where A+ is the most energy efficient and G the least energy efficient)"
        ),
    )
    property_type: str = pydantic.Field(
        max_length=76, description="Describes the type of building that is being inspected. Based on planning use class"
    )
    inspection_date: pydantic.NaiveDatetime = pydantic.Field(
        description="The date that the inspection was actually carried out by the energy assessor."
    )
    local_authority: str = pydantic.Field(
        max_length=9,
        description="Office for National Statistics (ONS) code. Local authority area in which the building is located",
    )
    transaction_type: str = pydantic.Field(
        max_length=51,
        description=(
            "Type of transaction that triggered EPC. One of: mandatory issue (marketed sale);"
            " mandatory issue (non-marketed sale); mandatory issue (property on construction);"
            " mandatory issue (property to let); voluntary re-issue (a valid epc is already lodged);"
            " voluntary (no legal requirement for an epc); not recorded. Transaction types may be changed over time."
        ),
    )
    new_build_benchmark: str = pydantic.Field(
        max_length=6, description="The Benchmark value of new build stock for this type of building"
    )
    existing_stock_benchmark: str = pydantic.Field(
        max_length=5, description="The Benchmark value of existing stock for this type of building"
    )
    building_level: str = pydantic.Field(
        max_length=1, description="Building Complexity Level based on Energy Assessor National Occupation Standards."
    )
    special_energy_uses: str | None = pydantic.Field(
        description="Special energy uses discounted. This only appears on the Recommendations Report."
    )
    standard_emissions: float | None = pydantic.Field(
        description=(
            "Standard Emission Rate is determined by applying a fixed improvement"
            " factor to the emissions from a reference building. (kg CO₂/m²/year)."
        )
    )
    target_emissions: float | None = pydantic.Field(
        description=(
            "The target emission rate is the minimum energy performance requirement"
            " (required by Building Regulation) for a new non- domestic building (kg CO₂/m²/year)."
        )
    )
    typical_emissions: float | None = pydantic.Field(description="Typical Emission Rate.")
    building_emissions: float | None = pydantic.Field(
        description="Building Emissions Rate. Annual CO₂ emissions from the building. Decimal (kg CO₂/m²)"
    )
    primary_energy: float | None = pydantic.Field(
        description="Displayed on the non-domestic EPC as primary energy use (kWh/m2 per year)", default=None
    )
    recommendations: list[NonDomesticRecommendation] | None = pydantic.Field(
        description="List of recommendations for this site", default=None
    )

    @pydantic.field_validator("other_fuel_desc", "special_energy_uses", "renewable_sources", mode="before", check_fields=False)
    def remove_blank_strings_epc(cls, v: str) -> str | None:
        """Remove whitespace from EPC and return None if empty."""
        v = v.strip()
        if not v:
            return None
        return v

    @pydantic.field_validator(
        "standard_emissions", "target_emissions", "typical_emissions", "building_emissions", mode="before", check_fields=True
    )
    def remove_blank_floats_epc(cls, v: str | float) -> float | None:
        """Remove whitespace from float values and replace empties with None."""
        if isinstance(v, float):
            return v
        v = v.strip()
        if not v:
            return None
        return float(v)
