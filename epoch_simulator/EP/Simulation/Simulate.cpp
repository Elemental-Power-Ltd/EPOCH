#include "Simulate.hpp"

#include <chrono>

#include "Assets.h"
#include "Config.h"
#include "Eload.h"
#include "RGen.h"
#include "Grid.h"
#include "Hload.h"
#include "Costs.h"


FullSimulationResult simulateScenario(const HistoricalData& historicalData, std::vector<std::pair<std::string, float>> paramSlice)
{
	/*CALCULATIVE SECTION - START PROFILING */
	auto start = std::chrono::high_resolution_clock::now(); //start runtime clock

	Config myConfig; // initialise a config object with default data

	// Change the config parameters to the current set of values in the parameter grid
	for (size_t i = 0; i < paramSlice.size(); ++i) {
		if (myConfig.param_map_float.find(paramSlice[i].first) != myConfig.param_map_float.end()) {
			myConfig.set_param_float(paramSlice[i].first, paramSlice[i].second);
			//			myConfig.print_param_float(paramSlice[i].first);
		}
		else {
			myConfig.set_param_int(paramSlice[i].first, paramSlice[i].second);
			//			myConfig.print_param_int(paramSlice[i].first);
		}

	}

	int hours = myConfig.calculate_timesteps(); // number of hours is a float in case we need sub-hourly timewindows

	Eload MountEload(myConfig.getESS_aux_load()); //create a Eload object called Mount_eload and pass the total ESS aux_load to it

	year_TS hotel_eload(hours);
	hotel_eload.setTSvalues(historicalData.hotel_eload_data);
	hotel_eload.scaleTSvalues(myConfig.getFixed_load1_scalar()); // scale the data
	MountEload.writeTS_Fix_load_1(hotel_eload); // set the values with the imported hotel load data

	year_TS ev_eload(hours);
	ev_eload.setTSvalues(historicalData.ev_eload_data);
	ev_eload.scaleTSvalues(myConfig.getFixed_load2_scalar());
	MountEload.writeTS_Fix_load_2(ev_eload); // set the values with the imported hotel load data
	MountEload.calculateTS_ESS_aux_load(); // calculate ESS aux load 
	MountEload.calculateTotal_fix_load(); // Calculate total fixed load by adding TS together

	//year_TS fixed_eload(hours);
	//fixed_eload = MountEload.getTS_Total_fix_load(); // create a new timeseries of total fixed load

	// check the Rgen data is all of the same size.
	if (historicalData.RGen_data_1.size() != historicalData.RGen_data_2.size() ||
		historicalData.RGen_data_1.size() != historicalData.RGen_data_3.size() ||
		historicalData.RGen_data_1.size() != historicalData.RGen_data_4.size()
		) {
		std::cerr << "R_Gen vectors are not of the same size!" << std::endl;
		throw std::exception();
	}

	RGen MountRGen; // Create RGen object called MountRGen 

	year_TS RGen_1(hours); //create Rgen TS objects
	year_TS RGen_2(hours);
	year_TS RGen_3(hours);
	year_TS RGen_4(hours);

	RGen_1.setTSvalues(historicalData.RGen_data_1); // set the values with the imported RGen data
	RGen_1.scaleTSvalues(myConfig.getScalarRG1()); // scale RGen with ScalarRG1 in config
	MountRGen.writeTS_RGen_1(RGen_1); //send scaled values to RGen1

	RGen_2.setTSvalues(historicalData.RGen_data_2);
	RGen_2.scaleTSvalues(myConfig.getScalarRG2());
	MountRGen.writeTS_RGen_2(RGen_2);

	RGen_3.setTSvalues(historicalData.RGen_data_3);
	RGen_3.scaleTSvalues(myConfig.getScalarRG3());
	MountRGen.writeTS_RGen_3(RGen_3);

	RGen_4.setTSvalues(historicalData.RGen_data_4);
	RGen_4.scaleTSvalues(myConfig.getScalarRG4());
	MountRGen.writeTS_RGen_4(RGen_4); //send scaled values to RGen2

	MountRGen.calculateTS_RGen_total();

	std::vector<float> RGen_total_vect = MountRGen.getTS_RGen_total().getData(); // create vector of total RGen for output

	// ESUM tab begin 

	MountEload.calculateTS_Target_high_load(myConfig.getFlex_load_max()); 	// Timeseries for target high-flex load									

	MountEload.calculateTS_Total_target_load(); // Add high-flex target load to total fixed load

	MountEload.calculateTS_Total_load(); // Subtract timeseries for (small) parasitic load of ESS

	// Add ESS to total target load 
	year_TS ESUM = year_TS::subtract(MountEload.getTS_Total_load(), MountRGen.getTS_RGen_total()); // Final ESUM (electrical acitivity) is Total load minus Rgen 
	//[NOTE: For now it empircally PROVES 3x faster to Keep ESUM as a separate standalone TS (rather than store it in MountEload object, perhaps as it is continually referenced in the main ESS loop?) 
	std::vector<float> ESUM_vect = ESUM.getData(); // ESUM output vector for reporting
	// ESUM tab end

	// ESS tab begin
	ESS MountBESS(myConfig.getESS_charge_power(), myConfig.getESS_discharge_power(),
		myConfig.getESS_capacity(), myConfig.getESS_RTE(),
		myConfig.getESS_aux_load(), myConfig.getESS_start_SoC()); // Create an object of Battery class with config data... any parameter not passed to constructor will get default value

	MountBESS.initialise_chargekWh_TS(); // calculate BESS begining energy
	//std::cout << "Battery charge level begins at: " << TS1_chargekWh << "kWh... the game is afoot! \n"; //console progress update, can remove this output for speed

//These are steps on ESS tab for Opportunitic BESS alg # 1 (Charge mode from Rgen/ Discharge mode = Before grid) IMPORTANT: BELOW FORMULAE ONLY VALID FOR HOUR TIMESTEPS WHERE 1kWH = 1kW
//1. Calculate ESS available Discharge Power in TS1: DB4 = MIN(ESS_StartSoC,ESS_DisPwr)
//2. Calculate ESS available Charge Power in TS1: CB4 = MIN((ESS_Cap-ESS_StartSoC)/ESS_RTE,ESS_ChPwr)
//3. Calculate "Discharge mode = before grid" in TS1:  IB4=IF(ESum!B4>0,MIN(Esum!B4,ESS!DB4),0) NOTE: Dependency on Esum tab step 1, currently, ESUM[0]
//4. Calculate "Charge mode = Rgen only" in TS1: EB4=IF(ESum!B4<0,MIN(-Esum!B4,ESS!CB4),0) NOTE: Dependency on Esum tab step 1, currently, -ESUM[0]
//5. Calculate BESS actions in TS1 (Charge = B4 / Discharge = AB4 )
//6. Apply RTE, and update SoC in "ESS resulting state of charge (SoC)" TS1: BB4 = ESS_StartSoC-(AB4+B4*ESS_RTE)
//7. For TS2, Calculate ESS available Discharge Power for TS2 based on final SoC in TS1 and max discharge power DC4=MIN(BB4,ESS_DisPwr) 
//8. For TS2, Calculate ESS available Charge Power for TS2 based on final SoC in TS1 and max charge power CC4=MIN(ESS_Cap-BB4)/ESS_RTE,ESS_ChPwr)
//9. For TS2, Calculate "Discharge mode = before" in TS2: IC4 = IF(ESum!C4>0,MIN(ESum!C4,ESS!DC4),0) NOTE: Dependency on Esum tab step 2, currently, ESUM[1]
//10.For TS2, Calculate "Charge mode = Rgen only" EC4 = IF(Esum!C4<0,MIN(-ESum!C4,ESS!CC4),0) NOTE: Dependency on Esum tab step 2, currently, ESUM[1]
//11.Calculate BESS actions in TS1 (Charge = C4 / Discharge = AC4)
//12.For TS2, Caculate BESS actions and update SoC in "ESS resulting state of charge (SoC)" BC4 = BB4+C4*ESS_RTE-AC4
//13.Repeat actions 7-13 for remaining TS in time window

	//These are steps on ESS tab for Opportunitic BESS alg # 1 (Charge mode from Rgen/ Discharge mode = Before grid) IMPORTANT: BELOW FORMULAE ONLY VALID FOR HOUR TIMESTEPS WHERE 1kWH = 1kW
	//1. Calculate ESS available Discharge Power in TS1: DB4 = MIN(ESS_StartSoC,ESS_DisPwr)
	MountBESS.initialise_TS_ESS_available_discharge_power(myConfig.getTimeStep_hours());

	//2. Calculate ESS available Charge Power in TS1: CB4 = MIN((ESS_Cap-ESS_StartSoC)/ESS_RTE,ESS_ChPwr)
	MountBESS.initialise_TS_ESS_available_charge_power(myConfig.getTimeStep_hours());

	//3. Calculate "Discharge mode = before grid" in TS1:  IB4=IF(ESum!B4>0,MIN(Esum!B4,ESS!DB4),0) NOTE: Dependency on Esum tab step 1, currently, ESUM[0]
	MountBESS.initialise_TS_ESS_before_grid_discharge(ESUM.getValue(0), myConfig.getTimeStep_hours());

	//4. Calculate "Charge mode = Rgen only" in TS1: EB4=IF(ESum!B4<0,MIN(-Esum!B4,ESS!CB4),0) NOTE: Dependency on Esum tab step 1, currently, -ESUM[0]
	MountBESS.initialise_TS_ESS_Rgen_only_charge(ESUM.getValue(0), myConfig.getTimeStep_hours());

	//5. Calculate BESS actions in TS1 (Charge = B4 / Discharge = AB4 )
	MountBESS.initialise_TS_ESS_discharge(myConfig.getTimeStep_hours()); // flag that other charge mode engaged.

	MountBESS.initialise_TS_ESS_charge(myConfig.getTimeStep_hours()); // flag that other charge mode engaged.

	//6. Apply RTE, and update SoC in "ESS resulting state of charge (SoC)" TS1: BB4 = ESS_StartSoC-(AB4+B4*ESS_RTE)
	MountBESS.initialise_TS_ESS_resulting_SoC(myConfig.getTimeStep_hours());

	// main loop for ESS
	for (int timestep = 2; timestep < 8760; timestep++)
	{
		////7. For TS2+, Calculate ESS available Discharge Power for TS2 based on final SoC in TS1 and max discharge power DC4=MIN(BB4,ESS_DisPwr) 
		MountBESS.calculate_TS_ESS_available_discharge_power(myConfig.getTimeStep_hours(), timestep);

		////8. For TS2+, Calculate ESS available Charge Power for TS2 based on final SoC in TS1 and max charge power CC4=MIN(ESS_Cap-BB4)/ESS_RTE,ESS_ChPwr)
		MountBESS.calculate_TS_ESS_available_charge_power(myConfig.getTimeStep_hours(), timestep);

		////9. For TS2+, Calculate "Discharge mode = before" in TS2: IC4 = IF(ESum!C4>0,MIN(ESum!C4,ESS!DC4),0) NOTE: Dependency on Esum tab step 2, currently, ESUM[1]
		MountBESS.calculate_TS_ESS_before_grid_discharge(ESUM.getValue(timestep - 1), myConfig.getTimeStep_hours(), timestep);

		////10.For TS2+, Calculate "Charge mode = Rgen only" EC4 = IF(Esum!C4<0,MIN(-ESum!C4,ESS!CC4),0) NOTE: Dependency on Esum tab step 2, currently, ESUM[1]
		MountBESS.calculate_TS_ESS_Rgen_only_charge(ESUM.getValue(timestep - 1), myConfig.getTimeStep_hours(), timestep);

		////11.Calculate BESS actions in TS1 (Charge = C4 / Discharge = AC4)
		MountBESS.set_TS_ESS_discharge(myConfig.getTimeStep_hours(), timestep);

		MountBESS.set_TS_ESS_charge(myConfig.getTimeStep_hours(), timestep);

		////12.For TS2, Caculate BESS actions and update SoC in "ESS resulting state of charge (SoC)" BC4 = BB4+C4*ESS_RTE-AC4
		MountBESS.calculate_TS_ESS_resulting_SoC(timestep, myConfig.getTimeStep_hours());

		//13.Repeat actions 7-13 for remaining TS in time window
	}
	//Grid steps: have created the required vectors from ESUM and ESS, just need to add them etc here. Need a new class GRID to do functionality

	//Calculate Pre-grid balance = ESum!B4+ESS!B4-ESS!AB4
	Grid MountGrid(myConfig.getGridImport(), myConfig.getGridExport(), myConfig.getImport_headroom(), myConfig.getExport_headroom());

	MountGrid.writeTS_Pre_grid_balance(year_TS::subtract(ESUM, MountBESS.getTS_ESS_discharge())); // first subtract discharge, as in AB4
	//MountGrid.getTS_Pre_grid_balance().addto(MountBESS.getTS_ESS_charge()); // then add TS_ESScharge

	MountGrid.writeTS_Pre_grid_balance(year_TS::add(MountBESS.getTS_ESS_charge(), MountGrid.getTS_Pre_grid_balance()));
	//MountGrid.writeTS_Pre_grid_balance(Pre_grid_balance);

	//Calculate Grid Import = IF(BB4>0,MIN(BB4,Grid_imp),0)
	MountGrid.calculateGridImport(myConfig.calculate_timesteps());

	//Calculate Grid Export = IF(BB4<0,MIN(-BB4,Grid_exp),0)
	MountGrid.calculateGridExport(myConfig.calculate_timesteps());

	//Calculate Post-grid balance = BB4-B4+AB4
	MountGrid.writeTS_Post_grid_balance(year_TS::subtract(MountGrid.getTS_Pre_grid_balance(), MountGrid.getTS_GridImport()));
	//MountGrid.getTS_Post_grid_balance().addto(MountGrid.getTS_GridExport());

	MountGrid.writeTS_Post_grid_balance(year_TS::add(MountGrid.getTS_GridExport(), MountGrid.getTS_Post_grid_balance()));

	//Calulate Pre-Flex Import shortfall = IF(CB>0, CB4, 0)
	MountGrid.calculatePre_flex_import_shortfall(myConfig.calculate_timesteps());

	//Calculate Pre-Mop Curtailed Export = IF(CB<0,-CB4,0)
	MountGrid.calculatePre_Mop_curtailed_Export(myConfig.calculate_timesteps());

	//Actual Import shortfall (load curtailment) = IF(DB4>ESum!DB4,DB4-ESum!DB4,0)
	MountGrid.calculateActual_import_shortfall(myConfig.calculate_timesteps(), myConfig.getFlex_load_max());

	//Actual Curtailed Export = IF(EB>ESum!EB4,EB4-ESum!EB4,0)
	MountGrid.calculateActual_curtailed_export(myConfig.calculate_timesteps(), myConfig.getMop_load_max());

	//Finally need to pass actual flex Eload info for heat calculation

	//Hsum steps
	//Heat load: HSUM tab
	Hload MountHload;

	MountHload.writeTS_Heatload(historicalData.heatload_data);

	std::vector<float> heatload_vect = MountHload.getTS_Heatload().getData();

	//(heatload_data); // set the values with the imported hotel load data

	//Heat load
	//=XLOOKUP(($A31-1)*24+B$3,HLoad!$A$2:$A$8761,HLoad!$D$2:$D$8761,0,0)*ScalarHL1 // Just a way of wrangling into 365*24 in excel
	MountHload.getTS_Heatload().scaleTSvalues(myConfig.getScalarHL1());// scale with the main heat load scalar

	//Electrical Load scaled heat yield
	//ESum!BB4*ScalarHYield1+ESum!CB4*ScalarHYield2+Esum!KB4*ScalarHYield3+ESum!LB4*ScalarHYield4
	//

	MountHload.writeTS_Scaled_electrical_fix_heat_load_1(hotel_eload.getData());
	MountHload.writeTS_Scaled_electrical_fix_heat_load_2(ev_eload.getData());

	MountHload.scaleTS_Scaled_electrical_fix_heat_load_1(myConfig.getScalarHYield1()); //scale to heat yield scalar    
	MountHload.scaleTS_Scaled_electrical_fix_heat_load_2(myConfig.getScalarHYield2());

	//Actual_mop_load;// needs to be actual high flex load, calculated from Grid 
	Eload MountFlex;

	MountFlex.calculateActual_high_priority_load(myConfig.calculate_timesteps(), myConfig.getFlex_load_max(), MountGrid.getTS_Pre_flex_import_shortfall());
	MountFlex.calculateActual_low_priority_load(myConfig.calculate_timesteps(), myConfig.getMop_load_max(), MountGrid.getTS_Pre_Mop_curtailed_Export());

	//year_TS scaled_high_flex_heat = MountFlex.getTS_Actual_high_priority_load().scaleTSvalues_newTS(myConfig.getScalarHYield3());
	//year_TS scaled_low_flex_heat = MountFlex.getTS_Actual_low_priority_load().scaleTSvalues_newTS(myConfig.getScalarHYield4());

	MountHload.calculateElectrical_load_scaled_heat_yield(MountFlex.getTS_Actual_high_priority_load(), MountFlex.getTS_Actual_low_priority_load(), myConfig.getScalarHYield3(), myConfig.getScalarHYield4());

	//Heat shortfall
	//IF(B4>AB4,B4-AB4,0)
	MountHload.calculateHeat_shortfall(myConfig.calculate_timesteps());

	//Heat surplus
	//IF(B4<AB4,AB3-B4,0)
	MountHload.calculateHeat_surplus(myConfig.calculate_timesteps());

	//Data reporting
	std::vector<float> Total_load_vect = MountEload.getTS_Total_load().getData();
	//std::vector<float> ESUM_vect = ESUM.getData(); // this is created earlier to align with spreadsheet

	std::vector<float> ESS_available_discharge_power_vect = MountBESS.getTS_ESS_available_discharge_power().getData();
	std::vector<float> ESS_available_charge_power_vect = MountBESS.getTS_ESS_available_charge_power().getData();
	std::vector<float> TS_ESS_Rgen_only_charge_vect = MountBESS.getTS_ESS_Rgen_only_charge().getData();
	std::vector<float> TS_ESS_discharge_vect = MountBESS.getTS_ESS_discharge().getData();
	std::vector<float> TS_ESS_charge_vect = MountBESS.getTS_ESS_charge().getData();
	std::vector<float> TS_ESS_resulting_SoC_vect = MountBESS.getTS_ESS_resulting_SoC().getData();
	std::vector<float> TS_Pre_grid_balance_vect = MountGrid.getTS_Pre_grid_balance().getData();
	std::vector<float> TS_Grid_Import_vect = MountGrid.getTS_GridImport().getData();
	std::vector<float> TS_Grid_Export_vect = MountGrid.getTS_GridExport().getData();
	std::vector<float> TS_Post_grid_balance_vect = MountGrid.getTS_Post_grid_balance().getData();
	std::vector<float> TS_Pre_flex_import_shortfall_vect = MountGrid.getTS_Pre_flex_import_shortfall().getData();
	std::vector<float> TS_Pre_Mop_curtailed_export_vect = MountGrid.getTS_Pre_Mop_curtailed_Export().getData();
	std::vector<float> TS_Actual_import_shortfall_vect = MountGrid.getTS_Actual_import_shortfall().getData();
	std::vector<float> TS_Actual_curtailed_export_vect = MountGrid.getTS_Actual_curtailed_export().getData();
	std::vector<float> TS_Actual_high_priority_load_vect = MountFlex.getTS_Actual_high_priority_load().getData();
	std::vector<float> TS_Actual_low_priority_load_vect = MountFlex.getTS_Actual_low_priority_load().getData();
	std::vector<float> scaled_heatload_vect = MountHload.getTS_Heatload().getData();
	std::vector<float> Electrical_load_scaled_heat_yield_vect = MountHload.getTS_Electrical_load_scaled_heat_yield().getData();
	std::vector<float> TS_Heat_shortfall_vect = MountHload.getTS_Heat_shortfall().getData();
	std::vector<float> TS_Heat_surplus_vect = MountHload.getTS_Heat_surplus().getData();

	// Get parameter index
	float paramIndex;
	for (const auto& kv : paramSlice) {
		if (kv.first == "Parameter index") {
			paramIndex = kv.second;
		}
	}

	//  Calculate infrastructure costs section
	Costs myCost;

	float ESS_PCS_CAPEX = myCost.calculate_ESS_PCS_CAPEX(std::max(myConfig.getESS_charge_power(), myConfig.getESS_discharge_power()));
	//std::cout << "MyCost ESS_PCS_CAPEX " << ESS_PCS_CAPEX << std::endl;

	float ESS_PCS_OPEX = myCost.calculate_ESS_PCS_OPEX(std::max(myConfig.getESS_charge_power(), myConfig.getESS_discharge_power()));
	//std::cout << "MyCost ESS_PCS_OPEX " << ESS_PCS_OPEX << std::endl;

	float ESS_ENCLOSURE_CAPEX = myCost.calculate_ESS_ENCLOSURE_CAPEX(myConfig.getESS_capacity());
	//std::cout << "MyCost ENCLOSURE_CAPEX " << ESS_ENCLOSURE_CAPEX << std::endl;

	float ESS_ENCLOSURE_OPEX = myCost.calculate_ESS_ENCLOSURE_OPEX(myConfig.getESS_capacity());
	//std::cout << "MyCost ENCLOSURE_OPEX " << ESS_ENCLOSURE_OPEX << std::endl;

	float ESS_ENCLOSURE_DISPOSAL = myCost.calculate_ESS_ENCLOSURE_DISPOSAL(myConfig.getESS_capacity());
	//std::cout << "MyCost ENCLOSURE_DISPOSAL " << ESS_ENCLOSURE_DISPOSAL << std::endl;

	float PV_kWp_total = myConfig.getScalarRG1() + myConfig.getScalarRG2() + myConfig.getScalarRG3() + myConfig.getScalarRG4();

	float PVpanel_CAPEX = myCost.calculate_PVpanel_CAPEX(PV_kWp_total);
	//std::cout << "PVpanel_CAPEX " << PVpanel_CAPEX << std::endl;

	float PVBoP_CAPEX = myCost.calculate_PVBoP_CAPEX(PV_kWp_total);
	//std::cout << "PVBoP_CAPEX " << PVBoP_CAPEX << std::endl;

	float PVroof_CAPEX = myCost.calculate_PVroof_CAPEX(0); // there is no roof mount in the mount project example, need to add to input parameters
	//std::cout << "PVBoP_CAPEX " << PVroof_CAPEX << std::endl;

	float PVground_CAPEX = myCost.calculate_PVground_CAPEX(myConfig.getScalarRG1() + myConfig.getScalarRG2() + myConfig.getScalarRG3() + myConfig.getScalarRG4()); // there is no roof mount in the mount project example, need to add to input parameters
	//std::cout << "PVground_CAPEX " << PVground_CAPEX << std::endl;

	float PV_OPEX = myCost.calculate_PV_OPEX(PV_kWp_total);
	//std::cout << "PV_OPEX " << PV_OPEX << std::endl;

	float EV_CP_Cost = myCost.calculate_EV_CP_cost(0, 3, 0, 0); // need to add num EV charge points to Config
	//std::cout << "MyCost EV_CP_COST " << EV_CP_Cost << std::endl;

	float EV_CP_install = myCost.calculate_EV_CP_install(0, 3, 0, 0); // need to add num EV charge points to Config
	//std::cout << "MyCost EV_CP_Install " << EV_CP_install << std::endl;

	float Grid_CAPEX = myCost.calculate_Grid_CAPEX(std::max(0, 0)); // need to add aditional grid capacity max (imp/exp) and out to Config
	//std::cout << "MyCost Grid_CAPEX " << Grid_CAPEX << std::endl;

	float ASHP_CAPEX = myCost.calculate_ASHP_CAPEX(12.0); // need to add num HP capacity to Config
	//std::cout << "MyCost ASHP_CAPEX " << ASHP_CAPEX << std::endl;

	float ESS_kW = std::max(myConfig.getESS_charge_power(), myConfig.getESS_discharge_power());

	float annualised_project_cost = myCost.calculate_Project_annualised_cost(ESS_kW, myConfig.getESS_capacity(), PV_kWp_total, 0, 3, 0, 0, 0, 12.0);

	//std::cout << "MyCost total_project_annualised_cost " << annualised_project_cost << std::endl;

	float total_annualised_cost = myCost.calculate_total_annualised_cost(ESS_kW, myConfig.getESS_capacity(), PV_kWp_total, 0, 3, 0, 0, 0, 12.0);

	year_TS import_elec_prices;
	import_elec_prices.setallTSvalues(myConfig.getImport_kWh_price()); // for now, simply fix import price
	year_TS export_elec_prices;
	export_elec_prices.setallTSvalues(myConfig.getExport_kWh_price()); // for now, simply fix import price


	year_TS baseline_elec_load_no_HPL = year_TS::add(MountEload.getTS_Fix_load_1(), MountEload.getTS_Fix_load_2());
	//std::cout << "MyCost fix load 1 plus fix load 2 " << baseline_elec_load << std::endl;

	year_TS baseline_elec_load = year_TS::add(baseline_elec_load_no_HPL, MountFlex.getTS_Actual_high_priority_load());
	//std::cout << "Adding Actual high priority load " << baseline_elec_load << std::endl;

	//	myCost.calculate_baseline_elec_cost(baseline_elec_load_no_HPL, import_elec_prices);
	myCost.calculate_baseline_elec_cost(baseline_elec_load, import_elec_prices);

	year_TS baseline_heat_load = year_TS::add(MountHload.getTS_Heatload(), MountFlex.getTS_Actual_low_priority_load());
	year_TS import_fuel_prices;
	import_fuel_prices.setallTSvalues(12.2); // need to add a new config parameter here
	float boiler_efficiency = 0.9;

	myCost.calculate_baseline_fuel_cost(baseline_heat_load, import_fuel_prices, boiler_efficiency);

	myCost.calculate_scenario_elec_cost(MountGrid.getTS_GridImport(), import_elec_prices);

	myCost.calculate_scenario_fuel_cost(MountHload.getTS_Heat_shortfall(), import_fuel_prices);

	myCost.calculate_scenario_export_cost(MountGrid.getTS_GridExport(), export_elec_prices);

	myCost.calculate_scenario_cost_balance(total_annualised_cost);

	//========================================

	myCost.calculate_Project_CAPEX(ESS_kW, myConfig.getESS_capacity(), PV_kWp_total, 0, 3, 0, 0, 0, 12.0);

	//========================================

	myCost.calculate_payback_horizon();

	//========================================

	// Calculate time_dependent CO2e operational emissions section

	myCost.calculate_baseline_elec_CO2e(baseline_elec_load);

	myCost.calculate_baseline_fuel_CO2e(baseline_heat_load);

	myCost.calculate_scenario_elec_CO2e(MountGrid.getTS_GridImport());

	myCost.calculate_scenario_fuel_CO2e(MountHload.getTS_Heat_shortfall());

	myCost.calculate_scenario_export_CO2e(MountGrid.getTS_GridExport());

	myCost.calculate_scenario_carbon_balance();

	//========================================

	/*WRITE DATA SECTION - AFTER PROFILING CLOCK STOPPED*/

	//End profiling

	// calculate elaspsed run time
	auto end = std::chrono::high_resolution_clock::now();
	std::chrono::duration<double> elapsed = end - start;
	float runtime = static_cast<float>(elapsed.count());

	std::cout << "Runtime: " << elapsed.count() << " seconds" << std::endl; // print elapsed run time

	FullSimulationResult fullSimulationResult;

	fullSimulationResult.Rgen_total = RGen_total_vect;
	fullSimulationResult.Total_load = Total_load_vect;
	fullSimulationResult.ESUM = ESUM_vect;
	fullSimulationResult.ESS_available_discharge_power = ESS_available_discharge_power_vect;
	fullSimulationResult.ESS_available_charge_power = ESS_available_charge_power_vect;
	fullSimulationResult.ESS_Rgen_only_charge = TS_ESS_Rgen_only_charge_vect;
	fullSimulationResult.ESS_discharge = TS_ESS_discharge_vect;
	fullSimulationResult.ESS_charge = TS_ESS_charge_vect;
	fullSimulationResult.ESS_resulting_SoC = TS_ESS_resulting_SoC_vect;
	fullSimulationResult.Pre_grid_balance = TS_Pre_grid_balance_vect;
	fullSimulationResult.Grid_Import = TS_Grid_Import_vect;
	fullSimulationResult.Grid_Export = TS_Grid_Export_vect;
	fullSimulationResult.Post_grid_balance = TS_Post_grid_balance_vect;
	fullSimulationResult.Pre_flex_import_shortfall = TS_Pre_flex_import_shortfall_vect;
	fullSimulationResult.Pre_Mop_curtailed_export = TS_Pre_Mop_curtailed_export_vect;
	fullSimulationResult.Actual_import_shortfall = TS_Actual_import_shortfall_vect;
	fullSimulationResult.Actual_curtailed_export = TS_Actual_curtailed_export_vect;
	fullSimulationResult.Actual_high_priority_load = TS_Actual_high_priority_load_vect;
	fullSimulationResult.Actual_low_priority_load = TS_Actual_low_priority_load_vect;
	fullSimulationResult.heatload = heatload_vect;
	fullSimulationResult.scaled_heatload = scaled_heatload_vect;
	fullSimulationResult.Electrical_load_scaled_heat_yield = Electrical_load_scaled_heat_yield_vect;
	fullSimulationResult.Heat_shortfall = TS_Heat_shortfall_vect;
	fullSimulationResult.Heat_surplus = TS_Heat_surplus_vect;

	fullSimulationResult.runtime = runtime;
	fullSimulationResult.paramIndex = paramIndex;
	fullSimulationResult.total_annualised_cost = total_annualised_cost;
	fullSimulationResult.TS_project_CAPEX = myCost.get_project_CAPEX();
	fullSimulationResult.TS_scenario_cost_balance = myCost.get_scenario_cost_balance();
	fullSimulationResult.TS_payback_horizon_years = myCost.get_payback_horizon_years();
	fullSimulationResult.TS_scenario_carbon_balance = myCost.get_scenario_carbon_balance();

	return fullSimulationResult;

}

SimulationResult simulateScenarioAndSum(const HistoricalData& historicalData, std::vector<std::pair<std::string, float>> paramSlice)
{
	const FullSimulationResult& fullSimulationResult = simulateScenario(historicalData, paramSlice);

	SimulationResult simResult;
	
	// Commented out for performance as we only need the values at the bottom (for now)
	//simResult.Rgen_total = sumVector(fullSimulationResult.Rgen_total);
	//simResult.Total_load = sumVector(fullSimulationResult.Total_load);
	//simResult.ESUM = sumVector(fullSimulationResult.ESUM);
	//simResult.ESS_available_discharge_power = sumVector(fullSimulationResult.ESS_available_discharge_power);
	//simResult.ESS_available_charge_power = sumVector(fullSimulationResult.ESS_available_charge_power);
	//simResult.TS_ESS_Rgen_only_charge = sumVector(fullSimulationResult.TS_ESS_Rgen_only_charge);
	//simResult.TS_ESS_discharge = sumVector(fullSimulationResult.TS_ESS_discharge);
	//simResult.TS_ESS_charge = sumVector(fullSimulationResult.TS_ESS_charge);
	//simResult.TS_ESS_resulting_SoC = sumVector(fullSimulationResult.TS_ESS_resulting_SoC);
	//simResult.TS_Pre_grid_balance = sumVector(fullSimulationResult.TS_Pre_grid_balance);
	//simResult.TS_Grid_Import = sumVector(fullSimulationResult.TS_Grid_Import);
	//simResult.TS_Grid_Export = sumVector(fullSimulationResult.TS_Grid_Export);
	//simResult.TS_Post_grid_balance = sumVector(fullSimulationResult.TS_Post_grid_balance);
	//simResult.TS_Pre_flex_import_shortfall = sumVector(fullSimulationResult.TS_Pre_flex_import_shortfall);
	//simResult.TS_Pre_Mop_curtailed_export = sumVector(fullSimulationResult.TS_Pre_Mop_curtailed_export);
	//simResult.TS_Actual_import_shortfall = sumVector(fullSimulationResult.TS_Actual_import_shortfall);
	//simResult.TS_Actual_curtailed_export = sumVector(fullSimulationResult.TS_Actual_curtailed_export);
	//simResult.TS_Actual_high_priority_load = sumVector(fullSimulationResult.TS_Actual_high_priority_load);
	//simResult.TS_Actual_low_priority_load = sumVector(fullSimulationResult.TS_Actual_low_priority_load);
	//simResult.heatload = sumVector(fullSimulationResult.heatload);
	//simResult.scaled_heatload = sumVector(fullSimulationResult.scaled_heatload);
	//simResult.Electrical_load_scaled_heat_yield = sumVector(fullSimulationResult.Electrical_load_scaled_heat_yield);
	//simResult.TS_Heat_shortfall = sumVector(fullSimulationResult.TS_Heat_shortfall);
	//simResult.TS_Heat_surplus = sumVector(fullSimulationResult.TS_Heat_surplus);

	simResult.runtime = fullSimulationResult.runtime;
	simResult.paramIndex = fullSimulationResult.paramIndex;
	simResult.total_annualised_cost = fullSimulationResult.total_annualised_cost;
	simResult.TS_project_CAPEX = fullSimulationResult.TS_project_CAPEX;
	simResult.TS_scenario_cost_balance = fullSimulationResult.TS_scenario_cost_balance;
	simResult.TS_payback_horizon_years = fullSimulationResult.TS_payback_horizon_years;
	simResult.TS_scenario_carbon_balance = fullSimulationResult.TS_scenario_carbon_balance;

	return simResult;
}

float sumVector(const std::vector<float>& v) {
	return std::accumulate(v.begin(), v.end(), 0.0f);
}