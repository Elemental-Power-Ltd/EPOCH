#pragma once
//include"Timeseries.h";

class Grid
{
public:
	Grid (float GridImport = 0.0f, float GridExport = 0.0f, float Import_headroom = 0.0f, float Export_headroom = 0.0f,
	year_TS Pre_grid_balance = {}, year_TS TS_GridImport = {}, year_TS TS_GridExport = {}, year_TS TS_Pre_grid_balance = {}, year_TS TS_Post_grid_balance = {},
	year_TS TS_Pre_flex_import_shortfall = {}, year_TS TS_Pre_Mop_curtailed_Export = {}, year_TS TS_Actual_import_shortfall = {},
	year_TS TS_Actual_curtailed_export = {}, year_TS TS_Energy_balance = {})
	:GridImport(GridImport), GridExport(GridExport), Import_headroom(Import_headroom), Export_headroom(Export_headroom),
	TS_GridImport(TS_GridImport), TS_GridExport(TS_GridExport), TS_Pre_grid_balance(TS_Pre_grid_balance), TS_Post_grid_balance(TS_Post_grid_balance),
	TS_Pre_flex_import_shortfall(TS_Pre_flex_import_shortfall), TS_Pre_Mop_curtailed_Export(TS_Pre_Mop_curtailed_Export), 
	TS_Actual_import_shortfall(TS_Actual_import_shortfall), TS_Actual_curtailed_export(TS_Actual_curtailed_export), TS_Energy_balance(TS_Energy_balance)
	{}

	// Functionality
	float calculate_Grid_imp() // these functions account for headroom built in to Grid_connection to take import/export power peaks intratimestep
	{
		float Grid_imp = GridImport * (1-Import_headroom);
		return Grid_imp;
	}
	
	float calculate_Grid_exp()
	{
		float Grid_exp = GridExport * (1-Export_headroom);
		return Grid_exp;
	}


	void calculateGridImport(int timesteps) //Calculate Grid Import = IF(BB4>0,MIN(BB4,Grid_imp),0)
	{
		for (int index = 0; index < timesteps; index++)
		{
			float Pre_grid_balance_val = TS_Pre_grid_balance.getValue(index); // this is a member inside the Grid Object 
				if (Pre_grid_balance_val > 0)
				{
					float GridImport_new_value = std::min(Pre_grid_balance_val, calculate_Grid_imp());
					TS_GridImport.setValue(index, GridImport_new_value);
				}
				else
				{
					TS_GridImport.setValue(index, 0);
				}
		}
	return;
	}

	void calculateGridExport(int timesteps) //Calculate Grid Export = IF(BB4<0,MIN(-BB4,Grid_exp),0)
	{
		for (int index = 0; index < timesteps; index++)
		{
			float Pre_grid_balance_val = TS_Pre_grid_balance.getValue(index); // this is a member inside the Grid Object 
			if (Pre_grid_balance_val < 0)
			{
				float GridExport_new_value = std::min(-Pre_grid_balance_val, calculate_Grid_exp());
				TS_GridExport.setValue(index, GridExport_new_value);
			}
			else
			{
				TS_GridExport.setValue(index, 0);
			}
		}
		return;
	}


	//Calulate Pre-Flex Import shortfall = IF(CB>0, CB4, 0)

	void calculatePre_flex_import_shortfall(int timesteps) 
	{
		for (int index = 0; index < timesteps; index++)
		{
			float Post_grid_balance_val = TS_Post_grid_balance.getValue(index); // this is a member inside the Grid Object 
			if (Post_grid_balance_val > 0)
			{
				float Pre_flex_import_shortfall_new_value = Post_grid_balance_val;
				TS_Pre_flex_import_shortfall.setValue(index, Pre_flex_import_shortfall_new_value);
			}
			else
			{
				TS_Pre_flex_import_shortfall.setValue(index, 0);
			}
		}
		return;
	}

	//Calculate Pre-Mop Curtailed Export = IF(CB<0,-CB4,0)

	void calculatePre_Mop_curtailed_Export(int timesteps) //Calculate Grid Import =IF(CB<0,-CB4,0)
	{
		for (int index = 0; index < timesteps; index++)
		{
			float Post_grid_balance_val = TS_Post_grid_balance.getValue(index); // this is a member inside the Grid Object 
			if (Post_grid_balance_val < 0)
			{
				float Pre_Mop_curtailed_Export_new_value = -Post_grid_balance_val;
				TS_Pre_Mop_curtailed_Export.setValue(index, Pre_Mop_curtailed_Export_new_value);
			}
			else
			{
				TS_Pre_Mop_curtailed_Export.setValue(index, 0);
			}
		}
		return;
	}

	//Calculate actual Import shortfall (load curtailment) = IF(DB4>ESum!DB4,DB4-ESum!DB4,0)

	void calculateActual_import_shortfall(int timesteps, float Flex_load_max)
	{
		for (int index = 0; index < timesteps; index++)
		{
			float TS_Pre_flex_import_shortfall_val = TS_Pre_flex_import_shortfall.getValue(index); // this is a member inside the Grid Object 
			if (TS_Pre_flex_import_shortfall_val > Flex_load_max)
			{
				float Actual_import_shortfall_val_new_value = TS_Pre_flex_import_shortfall_val - Flex_load_max;
				TS_Actual_import_shortfall.setValue(index, Actual_import_shortfall_val_new_value);
			}
			else
			{
				TS_Actual_import_shortfall.setValue(index, 0);
			}
		}
		return;
	}

	void calculateActual_curtailed_export(int timesteps, float Mop_load_max)
	{
		for (int index = 0; index < timesteps; index++)
		{
			float TS_Pre_Mop_curtailed_export_val = TS_Pre_Mop_curtailed_Export.getValue(index); // this is a member inside the Grid Object 
			if (TS_Pre_Mop_curtailed_export_val > Mop_load_max)
			{
				float Actual_curtailed_export_val_new_value = TS_Pre_Mop_curtailed_export_val - Mop_load_max;
				TS_Actual_curtailed_export.setValue(index, Actual_curtailed_export_val_new_value);
			}
			else
			{
				TS_Actual_curtailed_export.setValue(index, 0);
			}
		}
		return;
	}

//Accessor member functions

	float getGridImport() const
	{
		return GridImport;
	}

	float getGridExport() const
	{
		return GridExport;
	}
	
	float getImport_headroom() const
	{
		return Import_headroom;
	}
		
	float getExport_headroom() const
	{
		return Export_headroom;
	}

//Accessor member functions for TS_year

	year_TS getTS_GridImport() const
	{
		return TS_GridImport;
	} 
	
	year_TS  getTS_GridExport() const
	{
		return TS_GridExport;
	}
	
	year_TS getTS_Pre_grid_balance() // not constant as want to modify 
	{
		return TS_Pre_grid_balance;
	}

	year_TS getTS_Post_grid_balance() 
	{
		return TS_Post_grid_balance;
	}

	year_TS getTS_Pre_flex_import_shortfall() const
	{
		return TS_Pre_flex_import_shortfall;
	}

	year_TS getTS_Pre_Mop_curtailed_Export() const
	{
		return TS_Pre_Mop_curtailed_Export;
	}

	year_TS getTS_Actual_import_shortfall() const
	{
		return TS_Actual_import_shortfall;
	}

	year_TS getTS_Actual_curtailed_export() const
	{
		return TS_Actual_curtailed_export;
	}

	year_TS getTS_Energy_balance() const
	{
		return TS_Energy_balance;
	}

	//Write functions for TS_year

	void writeTS_Pre_grid_balance(year_TS inputTS)
	{
		TS_Pre_grid_balance = inputTS;
		return;
	}

	void writeTS_Post_grid_balance(year_TS inputTS)
	{
		TS_Post_grid_balance = inputTS;
		return;
	}

	void writeTS_Pre_flex_import_shortfall(year_TS inputTS)
	{
		TS_Pre_flex_import_shortfall = inputTS;
		return;
	}

	void writeTS_Pre_Mop_curtailed_Export(year_TS inputTS)
	{
		TS_Pre_Mop_curtailed_Export = inputTS;
		return;
	}



private:
	float GridImport;
	float GridExport;
	float Import_headroom;
	float Export_headroom;
	year_TS TS_GridImport;
	year_TS TS_GridExport;
	year_TS TS_Pre_grid_balance;
	year_TS TS_Post_grid_balance;
	year_TS TS_Pre_flex_import_shortfall;
	year_TS TS_Pre_Mop_curtailed_Export;
	year_TS TS_Actual_import_shortfall;
	year_TS TS_Actual_curtailed_export;
	year_TS TS_Energy_balance;
};

