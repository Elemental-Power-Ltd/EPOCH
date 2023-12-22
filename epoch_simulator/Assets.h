#pragma once
//include "Timeseries.h"
//#include<vector>
#include<algorithm>
#ifndef ASSETS_H
#define ASSETS_H

class ESS {

public:
    ESS(// ESS fixed params
        float ESS_charge_power = 0.0f, float ESS_discharge_power = 0.0f,
        float ESS_capacity = 0.0f, float ESS_RTE = 0.0f, float ESS_aux_load = 0.0f, float ESS_start_SoC = 0.0f,
        int ESS_charge_mode = 1, int ESS_discharge_mode = 1,

        // ESS intialisation variables (TS one)
        float chargekWh_TS1 = 0.0f,
        float ESS_available_discharge_power_TS1 = 0.0f, float ESS_available_charge_power_TS1 = 0.0f,
        float ESS_discharge_TS1 = 0.0f, float ESS_charge_TS1 = 0.0f,
        float ESS_resulting_SoC_TS1 = 0.0f,

        // ESS timestep variables
        float chargekWh_TS = 0.0f,
        float ESS_available_discharge_power_TS = 0.0f, float ESS_available_charge_power_TS = 0.0f,
        float ESS_discharge_TS = 0.0f, float ESS_charge_TS = 0.0f,
        float ESS_resulting_SoC_TS = 0.0f,

        // Timeseries 
        year_TS TS_ESS_charge = {}, year_TS TS_ESS_discharge = {}, year_TS TS_ESS_Rgen_only_charge = {},
        year_TS TS_ESS_before_grid_discharge = {}, year_TS TS_ESS_resulting_SoC = {},
        year_TS TS_ESS_available_charge_power = {}, year_TS TS_ESS_available_discharge_power = {})

        : ESS_charge_power(ESS_charge_power), ESS_discharge_power(ESS_discharge_power),
        ESS_capacity(ESS_capacity), ESS_RTE(ESS_RTE), ESS_aux_load(ESS_aux_load), ESS_start_SoC(ESS_start_SoC),
        ESS_charge_mode(ESS_charge_mode), ESS_discharge_mode(ESS_discharge_mode),

        chargekWh_TS1(chargekWh_TS1), ESS_available_discharge_power_TS1(ESS_available_discharge_power_TS1),
        ESS_available_charge_power_TS1(ESS_available_charge_power_TS1), ESS_discharge_TS1(ESS_discharge_TS1),
        ESS_charge_TS1(ESS_charge_TS1), ESS_resulting_SoC_TS1(ESS_resulting_SoC_TS1),

        chargekWh_TS(chargekWh_TS), ESS_available_discharge_power_TS(ESS_available_discharge_power_TS),
        ESS_available_charge_power_TS(ESS_available_charge_power_TS), ESS_discharge_TS(ESS_discharge_TS),
        ESS_charge_TS(ESS_charge_TS), ESS_resulting_SoC_TS(ESS_resulting_SoC_TS),

        TS_ESS_charge(TS_ESS_charge), TS_ESS_discharge(TS_ESS_discharge), TS_ESS_Rgen_only_charge(TS_ESS_Rgen_only_charge),
        TS_ESS_before_grid_discharge(TS_ESS_before_grid_discharge), TS_ESS_resulting_SoC(TS_ESS_resulting_SoC),
        TS_ESS_available_charge_power(TS_ESS_available_charge_power), TS_ESS_available_discharge_power(TS_ESS_available_discharge_power) {}

private:
    float ESS_charge_power;
    float ESS_discharge_power;
    float ESS_capacity;
    float ESS_RTE;
    float ESS_aux_load;
    float ESS_start_SoC;
    int ESS_charge_mode;
    int ESS_discharge_mode;

    // ESS initialisation variables
    float chargekWh_TS1;
    float ESS_available_discharge_power_TS1;
    float ESS_available_charge_power_TS1;
    float ESS_discharge_TS1;
    float ESS_charge_TS1;
    float ESS_resulting_SoC_TS1;

    // ESS timestep variables
    float chargekWh_TS;
    float ESS_available_discharge_power_TS;
    float ESS_available_charge_power_TS;
    float ESS_discharge_TS;
    float ESS_charge_TS;
    float ESS_resulting_SoC_TS;

    year_TS TS_ESS_charge;
    year_TS TS_ESS_discharge;
    year_TS TS_ESS_Rgen_only_charge;
    year_TS TS_ESS_before_grid_discharge;
    year_TS TS_ESS_available_charge_power;
    year_TS TS_ESS_available_discharge_power;
    year_TS TS_ESS_resulting_SoC;

    //~ESS() // Destructor 
// public  data objects
//  

public:
    // Member functions: ESS initialisation (only act on first time-step)
    void initialise_chargekWh_TS()
    {
        chargekWh_TS = ESS_start_SoC * ESS_capacity;
        return;
    }

    void initialise_TS_ESS_available_discharge_power(float timestep_hours = 1.0f) {
        float ESS_start_SoC_power = ESS_start_SoC * ESS_capacity / timestep_hours; // calculate kW power from energy kWh (NEEDS attention for TS=! 1.)
        float TS1_discharge_power = std::min(ESS_start_SoC_power, ESS_discharge_power);
        TS_ESS_available_discharge_power.setValue(0, TS1_discharge_power);
        ESS_available_discharge_power_TS1 = TS1_discharge_power;
        return;
    }

    void initialise_TS_ESS_available_charge_power(float timestep_hours = 1.0f) {
        float ESS_start_SoC_power = ESS_start_SoC * ESS_capacity / timestep_hours; // calculate kW power from energy kWh 
        float charge_potential = (ESS_capacity - ESS_start_SoC_power) / ESS_RTE;
        float TS1_charge_power = std::min(charge_potential, ESS_charge_power);
        TS_ESS_available_charge_power.setValue(0, TS1_charge_power);
        ESS_available_charge_power_TS1 = TS1_charge_power;
        return;
    }

    void initialise_TS_ESS_before_grid_discharge(float Esum_TS1, float timestep_hours = 1.0f) {
        float TS1_before_grid_discharge;
        if (Esum_TS1 > 0)
        {
            TS1_before_grid_discharge = std::min(Esum_TS1, ESS_available_discharge_power_TS1);
        }
        else
        {
            TS1_before_grid_discharge = 0;
        }
        // calculate kW power from energy kWh 
        TS_ESS_before_grid_discharge.setValue(0, TS1_before_grid_discharge);
        return;
    }

    void initialise_TS_ESS_Rgen_only_charge(float Esum_TS1, float timestep_hours = 1.0f) {
        float TS1_Rgen_only_charge;
        if (Esum_TS1 < 0)
        {
            TS1_Rgen_only_charge = std::min(-Esum_TS1, ESS_available_charge_power_TS1);
        }
        else
        {
            TS1_Rgen_only_charge = 0;
        }
        // calculate kW power from energy kWh 
        TS_ESS_Rgen_only_charge.setValue(0, TS1_Rgen_only_charge);
        return;
    }

    void initialise_TS_ESS_discharge(float timestep_hours = 1.0f){
        if (ESS_discharge_mode == 1)
        {
            float TS1_ESS_discharge = TS_ESS_before_grid_discharge.getValue(0);
            TS_ESS_discharge.setValue(0, TS1_ESS_discharge);
            ESS_discharge_TS1 = TS1_ESS_discharge;
        }
        else
        {
            TS_ESS_discharge.setValue(0, 999.9f);; // flag that other charge mode engaged.
            ESS_charge_TS1 = 999.9f;
        } 
        return;
    }

    void initialise_TS_ESS_charge(float timestep_hours = 1.0f) {
        if (ESS_charge_mode == 1)
        {
            float TS1_ESS_charge = TS_ESS_Rgen_only_charge.getValue(0);
            TS_ESS_charge.setValue(0, TS1_ESS_charge);
            ESS_charge_TS1 = TS1_ESS_charge;
        }
        else
        {
            TS_ESS_discharge.setValue(0, 999.9f);; // flag that other charge mode engaged.
            ESS_charge_TS1 = 999.9f;
        }
        return;
    }

    void initialise_TS_ESS_resulting_SoC(float timestep_hours = 1.0f) {
        float ESS_start_SoC_energy = ESS_start_SoC * ESS_capacity * timestep_hours; // calculate kW power from energy kWh
        ESS_resulting_SoC_TS1 = ESS_start_SoC_energy - (ESS_discharge_TS1 + ESS_charge_TS1 * ESS_RTE) * timestep_hours;// calculate resulting SoC energy from discharge / charge actions latter with RTE applied
        TS_ESS_resulting_SoC.setValue(0, ESS_resulting_SoC_TS1);
        return;
    }

    // Member functions: ESS calculations for TS2+

    void calculate_TS_ESS_available_discharge_power(float timestep_hours = 1.0f, int timestep = 2) {
        int timestep_index = timestep - 1; // the C++ vector index begins at 0 so, for example TS2 is index 1
        float prev_resulting_SoC = TS_ESS_resulting_SoC.getValue(timestep_index - 1);// get previous value of resulting SoC
        float ESS_prev_SoC_power = prev_resulting_SoC / timestep_hours; //energy to power 
        float TS_available_discharge_power = std::min(ESS_prev_SoC_power, ESS_discharge_power); // calculate based DC4 = MIN(BB4, ESS_DisPwr)
        TS_ESS_available_discharge_power.setValue(timestep_index, TS_available_discharge_power);
        return;
    }

    void calculate_TS_ESS_available_charge_power(float timestep_hours = 1.0f, int timestep = 2) {
        int timestep_index = timestep - 1; // the C++ vector index begins at 0 so, for example TS2 is index 1
        float prev_resulting_SoC = TS_ESS_resulting_SoC.getValue(timestep_index - 1); // calculate kW power from energy kWh 
        float ESS_prev_SoC_power = prev_resulting_SoC / timestep_hours; //energy to power 
        float charge_potential = (ESS_capacity - ESS_prev_SoC_power) / ESS_RTE; // get previous value of resulting SoC
        float TS_available_charge_power = std::min(charge_potential, ESS_charge_power); // CC4 = MIN(ESS_Cap - BB4) / ESS_RTE, ESS_ChPwr)
        TS_ESS_available_charge_power.setValue(timestep_index, TS_available_charge_power);
        return;
    }

    void calculate_TS_ESS_before_grid_discharge(float Esum_TS, float timestep_hours = 1.0f, int timestep = 2) {
        int timestep_index = timestep - 1; // the C++ vector index begins at 0 so, for example TS2 is index 1
        float ESS_dis_TS = TS_ESS_available_discharge_power.getValue(timestep_index);
        float TS_before_grid_discharge;
        if (Esum_TS > 0)
        {
            TS_before_grid_discharge = std::min(Esum_TS, ESS_dis_TS);
        }
        else
        {
            TS_before_grid_discharge = 0;
        }
        // calculate kW power from energy kWh 
        TS_ESS_before_grid_discharge.setValue(timestep_index, TS_before_grid_discharge); //TS2: IC4 = IF(ESum!C4 > 0, MIN(ESum!C4, ESS!DC4), 0) NOTE : Dependency on Esum tab step 2, currently, ESUM[2]
        return;
    }

    void calculate_TS_ESS_Rgen_only_charge(float Esum_TS, float timestep_hours = 1.0f, int timestep = 2) {
        int timestep_index = timestep - 1;
        float ESS_charge_TS = TS_ESS_available_charge_power.getValue(timestep_index);
        float TS_Rgen_only_charge;
        if (Esum_TS < 0)
        {
            TS_Rgen_only_charge = std::min(-Esum_TS, ESS_charge_TS);
        }
        else
        {
            TS_Rgen_only_charge = 0;
        }
        TS_ESS_Rgen_only_charge.setValue(timestep_index, TS_Rgen_only_charge); //EC4 = IF(Esum!C4<0,MIN(-ESum!C4,ESS!CC4),0)
        return;
    }

    void set_TS_ESS_discharge(float timestep_hours = 1.0f, int timestep = 2)
    {
        int timestep_index = timestep - 1;
        if (ESS_discharge_mode == 1)
        {
            float ESS_discharge_TS = TS_ESS_before_grid_discharge.getValue(timestep_index);
            TS_ESS_discharge.setValue(timestep_index, ESS_discharge_TS);
        }
        else
        {
            std::cout << "err: discharge_mode does not yet exist";
        }
        return;
    }

    void set_TS_ESS_charge(float timestep_hours = 1.0f, int timestep = 2)
    {
        int timestep_index = timestep - 1;
        if (ESS_charge_mode == 1)
        {
            float ESS_charge_TS = TS_ESS_Rgen_only_charge.getValue(timestep_index);
            TS_ESS_charge.setValue(timestep_index, ESS_charge_TS);
        }
        else
        {
            std::cout << "err: charge_mode does not yet exist";
        }
        return;
    }
    //12.For TS2, Caculate BESS actions and update SoC in "ESS resulting state of charge (SoC)" BC4 = BB4+C4*ESS_RTE-AC4
    // these functions account for headroom built in to Grid_connection to take import/export power peaks intratimestep

    void calculate_TS_ESS_resulting_SoC(int timestep = 2, float timestep_hours = 1.0f)
    {
        int timestep_index = timestep - 1;
        float TS_ESS_end_SoC_energy = TS_ESS_resulting_SoC.getValue(timestep_index - 1) + (timestep_hours * ((TS_ESS_charge.getValue(timestep_index) * ESS_RTE) - ((TS_ESS_discharge.getValue(timestep_index))))); // calculate kW power from energy kWh
        // calculate resulting SoC energy from discharge / charge actions latter with RTE applied convert from power to energy.
        TS_ESS_resulting_SoC.setValue(timestep_index, TS_ESS_end_SoC_energy);
        return;
    }

    // Accessor member functions

    float getESS_charge_power() const {
        return ESS_charge_power;
    }

    float getESS_discharge_power() const {
        return ESS_discharge_power;
    }

    float getESS_capacity() const {
        return ESS_capacity;
    }

    float getESS_RTE() const {
        return ESS_RTE;
    }

    float getESS_aux_load() const {
        return ESS_aux_load;
    }

    float getESS_start_SoC() const {
        return ESS_start_SoC;
    }

    int getESS_charge_mode() const {
        return ESS_charge_mode;
    }

    int getESS_discharge_mode() const {
        return ESS_discharge_mode;
    }

    //Timestep variable accessor member functions

    float getchargekWh_TS1() const {
        return chargekWh_TS1;
    }

    float getESS_available_discharge_power_TS1() const {
        return ESS_available_discharge_power_TS1;
    }

    float getESS_available_charge_power_TS1() const {
        return ESS_available_charge_power_TS1;
    }

    float getESS_discharge_TS1() const {
        return ESS_discharge_TS1;
    }

    float getESS_charge_TS1() const {
        return ESS_charge_TS1;
    }

    float getESS_resulting_SoC_TS1() const {
        return ESS_resulting_SoC_TS1;
    }

    float getchargekWh_TS() const {
        return chargekWh_TS;
    }

    float getESS_available_discharge_power_TS() const {
        return ESS_available_discharge_power_TS;
    }

    float getESS_available_charge_power_TS() const {
        return ESS_available_charge_power_TS;
    }

    float getESS_discharge_TS() const {
        return ESS_discharge_TS;
    }

    float getESS_charge_TS() const {
        return ESS_charge_TS;
    }

    float getESS_resulting_SoC_TS() const {
        return ESS_resulting_SoC_TS;
    }

    //TS accessor member functions

    year_TS getTS_ESS_charge() const {
        return TS_ESS_charge;
    }

    year_TS getTS_ESS_discharge() const {
        return TS_ESS_discharge;
    }

    year_TS getTS_ESS_Rgen_only_charge() const {
        return TS_ESS_Rgen_only_charge;
    }

    year_TS getTS_ESS_before_grid_discharge() const {
        return TS_ESS_before_grid_discharge;
    }

    year_TS getTS_ESS_resulting_SoC() const {
        return TS_ESS_resulting_SoC;
    }

    year_TS getTS_ESS_available_charge_power() const {
        return TS_ESS_available_charge_power;
    }

    year_TS getTS_ESS_available_discharge_power() const {
        return TS_ESS_available_discharge_power;
    }

   // Timestep variable write functions:

    void setchargekWh_TS1(float new_chargekWh_TS1){
        chargekWh_TS1 = new_chargekWh_TS1;
        return;
    }

    void setESS_available_discharge_power_TS1(float newESS_available_discharge_power_TS1) {
        ESS_available_discharge_power_TS1 = newESS_available_discharge_power_TS1;
        return;
    }

    void setESS_available_charge_power_TS1(float newESS_available_charge_power_TS1) {
        ESS_available_charge_power_TS1 = newESS_available_charge_power_TS1;
        return;
    }

    void setESS_discharge_TS1(float newESS_discharge_TS1) {
        ESS_discharge_TS1 = newESS_discharge_TS1;
        return;
    }

    void setESS_charge_TS1(float newESS_charge_TS1) {
        ESS_charge_TS1 = newESS_charge_TS1;
        return;
    }

    void setESS_resulting_SoC_TS1(float newESS_resulting_SoC_TS1) {
        ESS_resulting_SoC_TS1 = newESS_resulting_SoC_TS1;
        return;
    }

    void setchargekWh_TS(float new_chargekWh_TS) {
        chargekWh_TS = new_chargekWh_TS;
        return;
    }

    void setESS_available_discharge_power_TS(float newESS_available_discharge_power_TS) {
        ESS_available_discharge_power_TS = newESS_available_discharge_power_TS;
        return;
    }

    void setESS_available_charge_power_TS(float newESS_available_charge_power_TS) {
        ESS_available_charge_power_TS = newESS_available_charge_power_TS;
        return;
    }

    void setESS_discharge_TS(float newESS_discharge_TS) {
        ESS_discharge_TS = newESS_discharge_TS;
        return;
    }

    void setESS_charge_TS(float newESS_charge_TS) {
        ESS_charge_TS = newESS_charge_TS;
        return;
    }

    void setESS_resulting_SoC_TS(float newESS_resulting_SoC_TS) {
        ESS_resulting_SoC_TS = newESS_resulting_SoC_TS;
        return;
    }

};

#endif // ASSETS_H
