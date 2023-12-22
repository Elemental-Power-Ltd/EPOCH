#pragma once
class Costs
{
public:

	Costs(float baseline_elec_cost_val = 0.0f, float baseline_fuel_cost_val = 0.0f, float scenario_import_cost_val = 0.0f,
		float scenario_fuel_cost_val = 0.0f,float scenario_export_cost_val = 0.0f, float scenario_cost_balance_val = 0.0f, 
		float project_CAPEX_val = 0.0f, float payback_horizon_years_val = 0.0f, float baseline_elec_CO2e_val = 0.0f, 
		float baseline_fuel_CO2e_val = 0.0f, float scenario_elec_CO2e_val = 0.0f, float scenario_fuel_CO2e_val = 0.0f, 
		float scenario_export_CO2e_val = 0.0f
		)
		: baseline_elec_cost(baseline_elec_cost_val), baseline_fuel_cost(baseline_fuel_cost_val), scenario_import_cost(scenario_import_cost_val),
		scenario_fuel_cost(scenario_fuel_cost_val), scenario_export_cost(scenario_export_cost_val), scenario_cost_balance(scenario_cost_balance_val),
		project_CAPEX(project_CAPEX_val), payback_horizon_years(payback_horizon_years_val), baseline_elec_CO2e(baseline_elec_CO2e_val),
		baseline_fuel_CO2e(baseline_fuel_CO2e_val), scenario_elec_CO2e(scenario_elec_CO2e_val), scenario_fuel_CO2e(scenario_fuel_CO2e_val), 
		scenario_export_CO2e(scenario_export_CO2e_val)
	{}
	
	//ESS COSTS

	float calculate_ESS_PCS_CAPEX(float ESS_kW) // these functions account for headroom built in to Grid_connection to take import/export power peaks intratimestep
	{
		// thresholds in kW units
		float small_thresh = 50;
		float mid_thresh = 1000;

		// costs in £ / kW
		float small_cost = 250.0;
		float mid_cost = 125.0;
		float large_cost = 75.0;

		float ESS_PCS_CAPEX = 0;

		if (ESS_kW < small_thresh)
		{
			ESS_PCS_CAPEX = small_cost * ESS_kW;
		}

		else if (small_thresh < ESS_kW && ESS_kW < mid_thresh)
		{
			ESS_PCS_CAPEX = (small_cost * small_thresh) + ((ESS_kW - small_thresh) * mid_cost);
		}

		else if (ESS_kW > mid_thresh)
		{
			ESS_PCS_CAPEX = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((ESS_kW - small_thresh - mid_thresh) * large_cost);
		}

		return ESS_PCS_CAPEX;
	}

	float calculate_ESS_PCS_OPEX(float ESS_kW)
	{
		// threholds in kW units
		float small_thresh = 50;
		float mid_thresh = 1000;

		// costs in £ / kW
		float small_cost = 8.0;
		float mid_cost = 4.0;
		float large_cost = 1.0;

		float ESS_PCS_OPEX = 0;

		if (ESS_kW < small_thresh)
		{
			ESS_PCS_OPEX = small_cost * ESS_kW;
		}

		else if (small_thresh < ESS_kW && ESS_kW < mid_thresh)
		{
			ESS_PCS_OPEX = (small_cost * small_thresh) + ((ESS_kW - small_thresh) * mid_cost);
		}

		else if (ESS_kW > mid_thresh)
		{
			ESS_PCS_OPEX = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((ESS_kW - small_thresh - mid_thresh) * large_cost);
		}

		return ESS_PCS_OPEX;
	}

	float calculate_ESS_ENCLOSURE_CAPEX(float ESS_kWh)
	{
		// threholds in kW units
		float small_thresh = 100;
		float mid_thresh = 2000;

		// costs in £ / kWh
		float small_cost = 480.0;
		float mid_cost = 360.0;
		float large_cost = 300.0;

		float ESS_ENCLOSURE_CAPEX = 0;

		if (ESS_kWh < small_thresh)
		{
			ESS_ENCLOSURE_CAPEX = small_cost * ESS_kWh;
		}

		else if (small_thresh < ESS_kWh && ESS_kWh < mid_thresh)
		{
			ESS_ENCLOSURE_CAPEX = (small_cost * small_thresh) + ((ESS_kWh - small_thresh) * mid_cost);
		}

		else if (ESS_kWh > mid_thresh)
		{
			ESS_ENCLOSURE_CAPEX = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((ESS_kWh - small_thresh - mid_thresh) * large_cost);
		}

		return ESS_ENCLOSURE_CAPEX;
	}

	float calculate_ESS_ENCLOSURE_OPEX(float ESS_kWh)
	{
		// threholds in kWh units
		float small_thresh = 100;
		float mid_thresh = 2000;

		// costs in £ / kWh
		float small_cost = 10.0;
		float mid_cost = 4.0;
		float large_cost = 2.0;

		float ESS_ENCLOSURE_OPEX = 0;

		if (ESS_kWh < small_thresh)
		{
			ESS_ENCLOSURE_OPEX = small_cost * ESS_kWh;
		}

		else if (small_thresh < ESS_kWh && ESS_kWh < mid_thresh)
		{
			ESS_ENCLOSURE_OPEX = (small_cost * small_thresh) + ((ESS_kWh - small_thresh) * mid_cost);
		}

		else if (ESS_kWh > mid_thresh)
		{
			ESS_ENCLOSURE_OPEX = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((ESS_kWh - small_thresh - mid_thresh) * large_cost);
		}

		return ESS_ENCLOSURE_OPEX;
	}

	float calculate_ESS_ENCLOSURE_DISPOSAL(float ESS_kWh)

	{// thresholds in kWh units
		float small_thresh = 100;
		float mid_thresh = 2000;

		// costs in £ / kWh
		float small_cost = 30.0;
		float mid_cost = 20.0;
		float large_cost = 15.0;

		float ESS_ENCLOSURE_DISPOSAL = 0;

		if (ESS_kWh < small_thresh)
		{
			ESS_ENCLOSURE_DISPOSAL = small_cost * ESS_kWh;
		}

		else if (small_thresh < ESS_kWh && ESS_kWh < mid_thresh)
		{
			ESS_ENCLOSURE_DISPOSAL = (small_cost * small_thresh) + ((ESS_kWh - small_thresh) * mid_cost);
		}

		else if (ESS_kWh > mid_thresh)
		{
			ESS_ENCLOSURE_DISPOSAL = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((ESS_kWh - small_thresh - mid_thresh) * large_cost);
		}

		return ESS_ENCLOSURE_DISPOSAL;
	}

	//PHOTOVOLTAIC COSTS (All units of kWp are DC)

	float calculate_PVpanel_CAPEX(float PV_kWp_total)
	{
		float small_thresh = 50;
		float mid_thresh = 1000;

		// costs in £ / kW DC
		float small_cost = 150.0;
		float mid_cost = 110.0;
		float large_cost = 95.0;

		float PVpanel_CAPEX = 0;

		if (PV_kWp_total < small_thresh)
		{
			PVpanel_CAPEX = small_cost * PV_kWp_total;
		}

		else if (small_thresh < PV_kWp_total && PV_kWp_total < mid_thresh)
		{
			PVpanel_CAPEX = (small_cost * small_thresh) + ((PV_kWp_total - small_thresh) * mid_cost);
		}

		else if (PV_kWp_total > mid_thresh)
		{
			PVpanel_CAPEX = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((PV_kWp_total - small_thresh - mid_thresh) * large_cost);
		}

		return PVpanel_CAPEX;
	}

	float calculate_PVBoP_CAPEX(float PV_kWp_total)

	{
		float small_thresh = 50;
		float mid_thresh = 1000;

		// costs in £ / kWp DC
		float small_cost = 120.0;
		float mid_cost = 88.0;
		float large_cost = 76.0;

		float PVBoP_CAPEX = 0;

		if (PV_kWp_total < small_thresh)
		{
			PVBoP_CAPEX = small_cost * PV_kWp_total;
		}

		else if (small_thresh < PV_kWp_total && PV_kWp_total < mid_thresh)
		{
			PVBoP_CAPEX = (small_cost * small_thresh) + ((PV_kWp_total - small_thresh) * mid_cost);
		}

		else if (PV_kWp_total > mid_thresh)
		{
			PVBoP_CAPEX = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((PV_kWp_total - small_thresh - mid_thresh) * large_cost);
		}

		return PVBoP_CAPEX;
	}

	float calculate_PVroof_CAPEX(float PV_kWp_total)
	{
		float small_thresh = 50;
		float mid_thresh = 1000;

		// costs in £ / kWp DC
		float small_cost = 250.0;
		float mid_cost = 200.0;
		float large_cost = 150.0;

		float PVroof_CAPEX = 0;

		if (PV_kWp_total < small_thresh)
		{
			PVroof_CAPEX = small_cost * PV_kWp_total;
		}

		else if (small_thresh < PV_kWp_total && PV_kWp_total < mid_thresh)
		{
			PVroof_CAPEX = (small_cost * small_thresh) + ((PV_kWp_total - small_thresh) * mid_cost);
		}

		else if (PV_kWp_total > mid_thresh)
		{
			PVroof_CAPEX = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((PV_kWp_total - small_thresh - mid_thresh) * large_cost);
		}

		return PVroof_CAPEX;
	}

	float calculate_PVground_CAPEX(float PV_kWp_total)
	{
		float small_thresh = 50;
		float mid_thresh = 1000;

		// costs in £ / kWp DC
		float small_cost = 150.0;
		float mid_cost = 125.0;
		float large_cost = 100.0;

		float PVground_CAPEX = 0;

		if (PV_kWp_total < small_thresh)
		{
			PVground_CAPEX = small_cost * PV_kWp_total;
		}

		else if (small_thresh < PV_kWp_total && PV_kWp_total < mid_thresh)
		{
			PVground_CAPEX = (small_cost * small_thresh) + ((PV_kWp_total - small_thresh) * mid_cost);
		}

		else if (PV_kWp_total > mid_thresh)
		{
			PVground_CAPEX = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((PV_kWp_total - small_thresh - mid_thresh) * large_cost);
		}

		return PVground_CAPEX;
	}

	float calculate_PV_OPEX(float PV_kWp_total)
	{
		float small_thresh = 50;
		float mid_thresh = 1000;

		// costs in £ / kWp DC
		float small_cost = 2.0;
		float mid_cost = 1.0;
		float large_cost = 0.50;

		float PV_OPEX = 0;

		if (PV_kWp_total < small_thresh)
		{
			PV_OPEX = small_cost * PV_kWp_total;
		}

		else if (small_thresh < PV_kWp_total && PV_kWp_total < mid_thresh)
		{
			PV_OPEX = (small_cost * small_thresh) + ((PV_kWp_total - small_thresh) * mid_cost);
		}

		else if (PV_kWp_total > mid_thresh)
		{
			PV_OPEX = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((PV_kWp_total - small_thresh - mid_thresh) * large_cost);
		}

		return PV_OPEX;
	}

	// EV charge point costs 

	// Cost model for EV charge points is based on per unit of each charger type, 7 kW, 22 kW, 50 kW and 150 kW

	float calculate_EV_CP_cost(int s7_EV_CP_number, int f22_EV_CP_number, int r50_EV_CP_number, int u150_EV_CP_number)
	{
		// costs in £ / unit (1 hd unit 2 connectors)
		float s7_EV_cost = 1200.00;
		float f22_EV_cost = 2500.00;
		float r50_EV_cost = 20000.00;
		float u150_EV_cost = 60000.00;

		float EV_CP_COST = (float(s7_EV_CP_number) * s7_EV_cost) + (float(f22_EV_CP_number) * f22_EV_cost) + (float(r50_EV_CP_number) * r50_EV_cost) + (float(u150_EV_CP_number) * u150_EV_cost);

		return EV_CP_COST;
	}

	float calculate_EV_CP_install(int s7_EV_CP_number, int f22_EV_CP_number, int r50_EV_CP_number, int u150_EV_CP_number)
	{
		// costs in £ / unit (1 hd unit 2 connectors)
		float s7_EV_install = 600.00;
		float f22_EV_install = 1000.00;
		float r50_EV_install = 3000.00;
		float u150_EV_install = 10000.00;

		float EV_CP_INSTALL = (float(s7_EV_CP_number) * s7_EV_install) + (float(f22_EV_CP_number) * f22_EV_install) + (float(r50_EV_CP_number) * r50_EV_install) + (float(u150_EV_CP_number) * u150_EV_install);

		return EV_CP_INSTALL;
	}

	// Grid upgrade costs

	float calculate_Grid_CAPEX(float kW_max)
	{
		float small_thresh = 50;
		float mid_thresh = 1000;

		// costs in £ / kW DC
		float small_cost = 240.0;
		float mid_cost = 160.0;
		float large_cost = 120.0;

		float Grid_CAPEX = 0;

		if (kW_max < small_thresh)
		{
			Grid_CAPEX = small_cost * kW_max;
		}

		else if (small_thresh < kW_max && kW_max < mid_thresh)
		{
			Grid_CAPEX = (small_cost * small_thresh) + ((kW_max - small_thresh) * mid_cost);
		}

		else if (kW_max > mid_thresh)
		{
			Grid_CAPEX = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((kW_max - small_thresh - mid_thresh) * large_cost);
		}

		return Grid_CAPEX;
	}

	// ASHP CAPEX costs

	float calculate_ASHP_CAPEX(float kW_elec)
	{
		float small_thresh = 10;
		float mid_thresh = 100;

		// costs in £ / kW DC
		float small_cost = 1000.0;
		float mid_cost = 1000.0;
		float large_cost = 1000.0;

		float ASHP_CAPEX = 0;

		if (kW_elec < small_thresh)
		{
			ASHP_CAPEX = small_cost * kW_elec;
		}

		else if (small_thresh < kW_elec && kW_elec < mid_thresh)
		{
			ASHP_CAPEX = (small_cost * small_thresh) + ((kW_elec - small_thresh) * mid_cost);
		}

		else if (kW_elec > mid_thresh)
		{
			ASHP_CAPEX = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((kW_elec - small_thresh - mid_thresh) * large_cost);
		}

		return ASHP_CAPEX;
	}

	float calculate_ESS_annualised_cost(float ESS_kW, float ESS_kWh, float PV_kWp_total) {
		float ESS_annualised_cost = ((calculate_ESS_PCS_CAPEX(ESS_kW) + calculate_ESS_ENCLOSURE_CAPEX(ESS_kWh) + calculate_ESS_ENCLOSURE_DISPOSAL(ESS_kWh)) / ESS_lifetime) + calculate_ESS_PCS_OPEX(ESS_kW) + calculate_ESS_ENCLOSURE_OPEX(ESS_kWh);
		return ESS_annualised_cost;
	}

	float calculate_PV_annualised_cost(float PV_kWp_total) {
		float PV_annualised_cost = ((calculate_PVpanel_CAPEX(PV_kWp_total) + calculate_PVBoP_CAPEX(PV_kWp_total) + calculate_PVroof_CAPEX(0) + calculate_PVground_CAPEX(PV_kWp_total)) / PV_panel_lifetime) + calculate_PV_OPEX(PV_kWp_total);
		return PV_annualised_cost;
	}

	float calculate_EV_CP_annualised_cost(int s7_EV_CP_number, int f22_EV_CP_number, int r50_EV_CP_number, int u150_EV_CP_number) {
		float EV_CP_annualised_cost = (calculate_EV_CP_cost(s7_EV_CP_number, f22_EV_CP_number, r50_EV_CP_number, u150_EV_CP_number) + calculate_EV_CP_install(s7_EV_CP_number, f22_EV_CP_number, r50_EV_CP_number, u150_EV_CP_number)) / EV_CP_lifetime;
		return EV_CP_annualised_cost;
	}

	float calculate_ASHP_annualised_cost(float kW_elec)

	{
		float ASHP_annualised_cost = calculate_ASHP_CAPEX(kW_elec) / ASHP_lifetime;
		return ASHP_annualised_cost;

	}

	float calculate_Grid_annualised_cost(float kw_grid_upgrade)
	{
		float Grid_annualised_cost = calculate_Grid_CAPEX(kw_grid_upgrade) / Grid_lifetime;
		return Grid_annualised_cost;
	}

	float calculate_Project_annualised_cost(float ESS_kW, float ESS_kWh, float PV_kWp_total, int s7_EV_CP_number, int f22_EV_CP_number, int r50_EV_CP_number, int u150_EV_CP_number, float kw_grid_upgrade, float kW_elec)
	{

		float ESS_CAPEX = calculate_ESS_PCS_CAPEX(ESS_kW) + calculate_ESS_ENCLOSURE_CAPEX(ESS_kWh) + calculate_ESS_ENCLOSURE_DISPOSAL(ESS_kWh);
		//std::cout << "in function ESS_CAPEX " << ESS_CAPEX << std::endl;
		float PV_CAPEX = calculate_PVpanel_CAPEX(PV_kWp_total) + calculate_PVBoP_CAPEX(PV_kWp_total) + calculate_PVroof_CAPEX(0) + calculate_PVground_CAPEX(PV_kWp_total);
		//std::cout << "in function PV_CAPEX " << PV_CAPEX << std::endl;
		float EV_CP_CAPEX = calculate_EV_CP_cost(s7_EV_CP_number, f22_EV_CP_number, r50_EV_CP_number, u150_EV_CP_number) + calculate_EV_CP_install(s7_EV_CP_number, f22_EV_CP_number, r50_EV_CP_number, u150_EV_CP_number);
		//std::cout << "in function EV_CP_CAPEX " << EV_CP_CAPEX << std::endl;
		float Grid_CAPEX = calculate_Grid_CAPEX(kw_grid_upgrade);
		//std::cout << "in function Grid_CAPEX " << Grid_CAPEX << std::endl;
		float ASHP_CAPEX = calculate_ASHP_CAPEX(kW_elec);
		//std::cout << "in function ASHP_CAPEX " << ASHP_CAPEX << std::endl;
		float Project_cost = (ESS_CAPEX + PV_CAPEX + EV_CP_CAPEX + ASHP_CAPEX) * project_plan_develop_EPC;
		//std::cout << "in function Project_cost  " << Project_cost << std::endl;
		float Project_cost_grid = Grid_CAPEX * project_plan_develop_Grid;
		//std::cout << "in function Project_cost_grid " << Project_cost_grid << std::endl;
		float Project_annualised_cost = (Project_cost + Project_cost_grid) / Project_lifetime;
		//std::cout << "in function Project_annualised_cost " << Project_annualised_cost << std::endl;
		return Project_annualised_cost;
	
	}

	void calculate_Project_CAPEX(float ESS_kW, float ESS_kWh, float PV_kWp_total, int s7_EV_CP_number, int f22_EV_CP_number, int r50_EV_CP_number, int u150_EV_CP_number, float kw_grid_upgrade, float kW_elec)
	{
		float ESS_CAPEX = calculate_ESS_PCS_CAPEX(ESS_kW) + calculate_ESS_ENCLOSURE_CAPEX(ESS_kWh) + calculate_ESS_ENCLOSURE_DISPOSAL(ESS_kWh);
		float PV_CAPEX = calculate_PVpanel_CAPEX(PV_kWp_total) + calculate_PVBoP_CAPEX(PV_kWp_total) + calculate_PVroof_CAPEX(0) + calculate_PVground_CAPEX(PV_kWp_total);
		float EV_CP_CAPEX = calculate_EV_CP_cost(s7_EV_CP_number, f22_EV_CP_number, r50_EV_CP_number, u150_EV_CP_number) + calculate_EV_CP_install(s7_EV_CP_number, f22_EV_CP_number, r50_EV_CP_number, u150_EV_CP_number);
		float Grid_CAPEX = calculate_Grid_CAPEX(kw_grid_upgrade);
		float ASHP_CAPEX = calculate_ASHP_CAPEX(kW_elec);
		float Project_cost = (ESS_CAPEX + PV_CAPEX + EV_CP_CAPEX + ASHP_CAPEX) * project_plan_develop_EPC;
		float Project_cost_grid = Grid_CAPEX * project_plan_develop_Grid;
		project_CAPEX = (ESS_CAPEX + PV_CAPEX + EV_CP_CAPEX + ASHP_CAPEX + Project_cost + Project_cost_grid);

		TS_project_CAPEX.setValue(0, project_CAPEX);

		return;
	}

	// Calculate annualised costs

	float calculate_total_annualised_cost(float ESS_kW, float ESS_kWh, float PV_kWp_total, int s7_EV_CP_number, int f22_EV_CP_number, int r50_EV_CP_number, int u150_EV_CP_number, float kw_grid_upgrade, float kW_elec)
	{
		float ESS_annualised_cost = ((calculate_ESS_PCS_CAPEX(ESS_kW) + calculate_ESS_ENCLOSURE_CAPEX(ESS_kWh) + calculate_ESS_ENCLOSURE_DISPOSAL(ESS_kWh)) / ESS_lifetime) + calculate_ESS_PCS_OPEX(ESS_kW) + calculate_ESS_ENCLOSURE_OPEX(ESS_kWh);
		
		float PV_annualised_cost = ((calculate_PVpanel_CAPEX(PV_kWp_total) + calculate_PVBoP_CAPEX(PV_kWp_total) + calculate_PVroof_CAPEX(0) + calculate_PVground_CAPEX(PV_kWp_total)) / PV_panel_lifetime) + calculate_PV_OPEX(PV_kWp_total);

		float EV_CP_annualised_cost = (calculate_EV_CP_cost(s7_EV_CP_number, f22_EV_CP_number, r50_EV_CP_number, u150_EV_CP_number) + calculate_EV_CP_install(s7_EV_CP_number, f22_EV_CP_number, r50_EV_CP_number, u150_EV_CP_number)) / EV_CP_lifetime;

		float Grid_annualised_cost = calculate_Grid_CAPEX(kw_grid_upgrade) / Grid_lifetime;

		float ASHP_annualised_cost = calculate_ASHP_CAPEX(kW_elec) / ASHP_lifetime;

		float Project_annualised_cost = ((calculate_ESS_PCS_CAPEX(ESS_kW) + calculate_ESS_ENCLOSURE_CAPEX(ESS_kWh) + calculate_ESS_ENCLOSURE_DISPOSAL(ESS_kWh) + calculate_PVpanel_CAPEX(PV_kWp_total)
			+ calculate_PVBoP_CAPEX(PV_kWp_total) + calculate_PVroof_CAPEX(0) + calculate_PVground_CAPEX(PV_kWp_total)
			+ calculate_EV_CP_cost(s7_EV_CP_number, f22_EV_CP_number, r50_EV_CP_number, u150_EV_CP_number) + calculate_EV_CP_install(s7_EV_CP_number, f22_EV_CP_number, r50_EV_CP_number, u150_EV_CP_number)
			+ calculate_ASHP_CAPEX(kW_elec)) * (project_plan_develop_EPC / Project_lifetime)) + ((calculate_Grid_CAPEX(kw_grid_upgrade)) * (project_plan_develop_Grid / Project_lifetime));

		float total_annualised_cost = Project_annualised_cost + ESS_annualised_cost + PV_annualised_cost + EV_CP_annualised_cost + Grid_annualised_cost + ASHP_annualised_cost;

		return total_annualised_cost;
	}

	// time-dependent scenario costs

	void calculate_baseline_elec_cost(year_TS baseline_elec_load, year_TS import_elec_prices)
	{
		float baseline_elec_load_sum = baseline_elec_load.sum();

		baseline_elec_cost = (baseline_elec_load_sum * import_elec_prices.getValue(0)) / 100; // just use fixed value for now

		//std::cout << "in function baseline_elec_cost " << baseline_elec_cost << std::endl;

		return;
	};

	void calculate_baseline_fuel_cost(year_TS baseline_heat_load, year_TS import_fuel_prices, float boiler_efficiency)
	{
		float baseline_heat_load_sum = baseline_heat_load.sum();

		baseline_fuel_cost = (baseline_heat_load_sum * import_fuel_prices.getValue(0) / boiler_efficiency) / 100; // this should be changed to divided by boiler efficiency

		//std::cout << "in function baseline_fuel_cost " << baseline_fuel_cost << std::endl;

		return;
	};

	void calculate_scenario_elec_cost(year_TS grid_import, year_TS import_elec_prices)
	{
		float grid_import_sum = grid_import.sum();

		scenario_import_cost = (grid_import_sum * import_elec_prices.getValue(0)) / 100; // just use fixed value for now

		//std::cout << "in function grid_import_cost " << grid_import_cost << std::endl;

		return;
	};

	void calculate_scenario_fuel_cost(year_TS total_heat_shortfall, year_TS import_fuel_prices)
	{
		float total_heat_shortfall_sum = total_heat_shortfall.sum();

		scenario_fuel_cost = (total_heat_shortfall_sum * import_fuel_prices.getValue(0) / boiler_efficiency) / 100; // this should be changed to divided by boiler efficiency

		//std::cout << "in function scenario_fuel_cost " << scenario_fuel_cost << std::endl;

		return;
	};

	void calculate_scenario_export_cost(year_TS grid_export, year_TS export_elec_prices)
	{
		float grid_export_sum = grid_export.sum();

		scenario_export_cost = (-grid_export_sum * export_elec_prices.getValue(0)) / 100; // just use fixed value for now

		//std::cout << "in function scenario_export_cost " << scenario_export_cost << std::endl;

		return;
	};

	void calculate_scenario_cost_balance(float Project_annualised_cost)
	{
		scenario_cost_balance = (baseline_elec_cost + baseline_fuel_cost) - (scenario_import_cost + scenario_fuel_cost + scenario_export_cost + Project_annualised_cost);

		TS_scenario_cost_balance.setValue(0, scenario_cost_balance);

		return;
	};

	void calculate_payback_horizon()
	{
		payback_horizon_years = project_CAPEX / scenario_cost_balance;

		TS_payback_horizon_years.setValue(0, payback_horizon_years);

		return;
	};


	// Member functions to calculate CO2 equivalent operational emissions costs

	void calculate_baseline_elec_CO2e(year_TS baseline_elec_load)
	{
		float baseline_elec_load_sum = baseline_elec_load.sum();

		baseline_elec_CO2e = (baseline_elec_load_sum * supplier_electricity_kg_CO2e); // just use fixed value for now

		return;
	};

	void calculate_baseline_fuel_CO2e(year_TS baseline_heat_load)
	{
		float baseline_heat_load_sum = baseline_heat_load.sum();

		baseline_fuel_CO2e = (baseline_heat_load_sum * LPG_kg_C02e / boiler_efficiency); // this should be changed to divided by boiler efficiency

		return;
	};

	void calculate_scenario_elec_CO2e(year_TS grid_import)
	{
		float grid_import_sum = grid_import.sum();

		scenario_elec_CO2e = (grid_import_sum * supplier_electricity_kg_CO2e); // just use fixed value for now

		return;
	};

	void calculate_scenario_fuel_CO2e(year_TS total_heat_shortfall)
	{
		float total_heat_shortfall_sum = total_heat_shortfall.sum();

		scenario_fuel_CO2e = (total_heat_shortfall_sum * LPG_kg_C02e / boiler_efficiency);

		return;

	};

	void calculate_scenario_export_CO2e(year_TS grid_export)
	{
		float grid_export_sum = grid_export.sum();

		scenario_export_CO2e = (-grid_export_sum * supplier_electricity_kg_CO2e);

		return;
	};

	void calculate_scenario_carbon_balance()
	{
		float scenario_balance = (baseline_elec_CO2e + baseline_fuel_CO2e) - (scenario_elec_CO2e + scenario_fuel_CO2e + scenario_export_CO2e);

		TS_scenario_carbon_balance.setValue(0, scenario_balance);

		return;
	};

	//Accessor member functions for TS_year
	year_TS getTS_annualised_cost()
	{
		return TS_annualised_cost;
	}

	year_TS getTS_project_CAPEX()
	{
		return TS_project_CAPEX;
	}

	year_TS getTS_scenario_cost_balance()
	{
		return TS_scenario_cost_balance;
	}

	year_TS getTS_payback_horizon_years()
	{
		return TS_payback_horizon_years;
	}

	year_TS getTS_scenario_carbon_balance()
	{
		return TS_scenario_carbon_balance;
	}

	// "hard wired" constants for the moment
	private:
		float project_plan_develop_EPC = 0.1f; // coefficient applied to local infrastructure CAPEX (decimal, not percentage)
		float project_plan_develop_Grid = 0.1f; // coefficient applied to grid infrastructure CAPEX (decimal, not percentage)

		float mains_gas_kg_C02e = 0.201f; // kg/kWh(w2h) 
		float LPG_kg_C02e = 0.239f; // kg/kWh (well2heat)
		float petrol_displace_kg_CO2e = 0.9037f; // every kWh that goes into an EV saves this much on the counterfactual of an ICE petrol vehicle

		float boiler_efficiency = 0.9f; // coefficient applied to convert gas kWh to heat kWh (decimal, not percentage)

		float mains_gas_price = 0.068f; // £/kWh  
		float LPG_cost_price = 0.122f; // £/kWh

		float supplier_electricity_kg_CO2e = 0.182f; //

		// plant lifetimes in years

		float ESS_lifetime = 15.0f;
		float PV_panel_lifetime = 25.0f;
		float EV_CP_lifetime = 15.0f;
		float Grid_lifetime = 25.0f;
		float ASHP_lifetime = 10.0f;
		float Project_lifetime = 10.0f;

		// Grid prices are currently part of the config

		float baseline_elec_cost;
		float baseline_fuel_cost;
		float scenario_import_cost;
		float scenario_fuel_cost;
		float scenario_export_cost;
		float scenario_cost_balance;
		float project_CAPEX;
		float payback_horizon_years;

		// variables for calculating CO2e operational emissions
		float baseline_elec_CO2e;
		float baseline_fuel_CO2e;
		float scenario_elec_CO2e;
		float scenario_fuel_CO2e;
		float scenario_export_CO2e;

		// time series for output
		year_TS TS_annualised_cost;
		year_TS TS_project_CAPEX;
		year_TS TS_scenario_cost_balance;
		year_TS TS_payback_horizon_years;
		year_TS TS_scenario_carbon_balance;

};

