#include <cmath>
#include <stdexcept>

#include "../../Definitions.hpp"



/*
* Calculate the SAP CO2 emissions factor.
*
* This emissions factor is used in the Energy Intensity Rating using
* a fixed set of CO2 factors that are updated yearly.
* 
* Parameters
* ----------
* gas_usage
*       kWh equivalent of natural gas consumed over the period
* elec_usage
*       kWh of electricity used over the period
* 
* Returns
* -------
* double
*       kg CO2e over the period according to SAP factors.
*/
double sap_co2_emissions(double gas_usage, double elec_usage) {
    /* Note that these are different between SAP 10.2 and RdSAP! */
    const double gas_co2_factor = 0.210;
    const double elec_co2_factor = 0.136;

    return gas_co2_factor * gas_usage + elec_co2_factor * elec_usage;
}

/*
* Calculate the SAP energy cost factor.
* 
* This cost factor is used in the Energy Intensity Rating using
* a fixed set of prices that are updated.
* 
* Parameters
* ----------
* gas_usage
*       kWh equivalent of natural gas consumed over the period
* elec_usage
*       kWh of electricity used over the period
* 
* Returns
* -------
* double
*       £ over the period according to SAP factors.
*/
double sap_energy_cost(double gas_usage, double elec_usage) {
    /* Note that these are different between SAP 10.2 and RdSAP! */
    const double gas_cost_factor = 3.64;
    const double elec_cost_factor = 16.49;

    return gas_usage * gas_cost_factor + elec_usage * elec_cost_factor;
}


/*
 * Calculate an Environmental Impact Rating for this building.
 *
 * The Environmental Impact Rating is used in non-domestic EPCs as a measure of how energy
 * efficient a building is to run.
 * You should use the SAP carbon factors to calculate this, as actual
 * fuels can vary significantly.
 * SAP 10.2 Section 14
 * https://files.bregroup.com/SAP/SAP%2010.2%20-%2011-04-2023.pdf
 *
 * The EI rating scale has been set so that EI 100 is achieved at zero net emissions.
 * It can rise above 100 if the dwelling is a net exporter of energy.
 * The EI rating is essentially independent of floor area.
 *
 * Parameters
 * ----------
 * co2_emissions
 *     SAP weighted CO2 emissions across a year across all fuels
 * total_floor_area
 *     Total floor area in m^2
 *
 * Returns
 * -------
 * int
 *     Integer Environmental Impact rating
 */
int environmental_impact_rating(double co2_emissions, double total_floor_area) {
    double carbon_factor = co2_emissions / (total_floor_area + 45.0);

    double ei_rating;
    if (carbon_factor >= 28.3) {
        ei_rating = 200.0 - 0.95 * std::log10(carbon_factor);
    }
    else {
        ei_rating = 100.0 - 1.34 * carbon_factor;
    }

    return static_cast<int>(std::max(std::round(ei_rating), 1.0));
}

/*
 * Calculate an Energy Cost Rating for this building.
 *
 * The Energy Cost Rating is used in Domestic EPCs as a measure of how energy
 * efficient a building is to run.
 * You should use the SAP energy cost factors to calculate this, as actual
 * tariffs can vary significantly.
 *
 * 100 is the best rating, and net exporters can have a rating above 100.
 * 1 is the worst rating.
 *
 * SAP 10.2 Section 13
 * https://files.bregroup.com/SAP/SAP%2010.2%20-%2011-04-2023.pdf
 *
 * Parameters
 * ----------
 * sap_energy_cost
 *     Total energy cost across all fuels as calculated by SAP methodology
 * total_floor_area
 *     Floor area in m^2 of this building
 *
 * Returns
 * -------
 * int
 *     Integer SAP rating likely between 1 and 100
 */
int energy_cost_rating(double sap_energy_cost, double total_floor_area) {
    double deflator = 0.36;
    double energy_cost_factor = deflator * sap_energy_cost / (total_floor_area + 45.0);
    double ec_rating;

    if (energy_cost_factor >= 3.5) {
        ec_rating = 108.8 - 120.5 * std::log10(energy_cost_factor);
    }
    else {
        ec_rating = 100.0 - 16.21 * energy_cost_factor;
    }

    return static_cast<int>(std::max(std::round(ec_rating), 1.0));
}


/*
 * Calculate a rating band (like you'd see on an EPC) for a given numerical rating.
 *
 * Numerical ratings are generally in the range 1-100 (but can be higher for net energy
 * exporters!), and are either Energy Cost Rating (£) or Energy Intensity Ratings (CO2e).
 *
 * Parameters
 * ----------
 * sap_rating
 *     Either an Energy Cost Rating or an Energy Intensity Rating
 *
 * Returns
 * -------
 * SAP letter band corresponding to this numerical rating
 */
RatingGrade rating_to_band(int sap_rating) {
    if (sap_rating >= 92) {
        return RatingGrade::A;
    }
    if (sap_rating >= 81) {
        return RatingGrade::B;
    }
    if (sap_rating >= 69) {
        return RatingGrade::C;
    }
    if (sap_rating >= 55) {
        return RatingGrade::D;
    }
    if (sap_rating >= 39) {
        return RatingGrade::E;
    }
    if (sap_rating >= 21) {
        return RatingGrade::F;
    }
    return RatingGrade::G;
}
