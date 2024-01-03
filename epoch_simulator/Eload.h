#pragma once

#include "Timeseries.h"

class Eload
{
	public:
		Eload(float ESS_aux_load = {}, year_TS TS_Fix_load_1 = {}, year_TS TS_Fix_load_2 = {}, year_TS TS_Total_fix_load = {},
			year_TS TS_Actual_high_priority_load = {}, year_TS TS_Actual_low_priority_load = {}, 
			year_TS TS_Target_high_load = {}, year_TS TS_Target_mop_load ={},
			year_TS TS_ESS_aux_load = {}, year_TS TS_Total_target_load = {}, year_TS TS_Total_load = {}, year_TS TS_ESUM = {})
			: ESS_aux_load(ESS_aux_load), TS_Fix_load_1(TS_Fix_load_1), TS_Fix_load_2(TS_Fix_load_2), TS_Total_fix_load(TS_Total_fix_load),
			TS_Actual_high_priority_load(TS_Actual_high_priority_load), TS_Actual_low_priority_load(TS_Actual_low_priority_load),
			TS_Target_high_load(TS_Target_high_load), TS_Target_mop_load(TS_Target_mop_load),
			TS_ESS_aux_load(TS_ESS_aux_load), TS_Total_target_load(TS_Total_target_load), TS_Total_load(TS_Total_load), TS_ESUM(TS_ESUM)
		{}

		//Functionality

		void writeTS_Fix_load_1(year_TS& inputTS)
		{
			TS_Fix_load_1 = inputTS;
			return;
		}

		void writeTS_Fix_load_2(year_TS& inputTS)
		{
			TS_Fix_load_2 = inputTS;
			return;
		}

		void calculateTotal_fix_load()
		{
			TS_Total_fix_load = year_TS::add(TS_Fix_load_1, TS_Fix_load_2);
			return;
		}



		void calculateActual_high_priority_load(int timesteps, float Flex_load_max,  year_TS TS_Pre_flex_import_shortfall)
		{
			for (int index = 0; index < timesteps; index++)
			{
				float TS_Pre_flex_import_shortfall_val = TS_Pre_flex_import_shortfall.getValue(index); // this is a member inside the Grid Object 
				float Actual_high_priority_load_val;
				if (TS_Pre_flex_import_shortfall_val > Flex_load_max)
				{
					TS_Actual_high_priority_load.setValue(index, 0);
				}
				else
				{
					Actual_high_priority_load_val = Flex_load_max - TS_Pre_flex_import_shortfall_val;
					TS_Actual_high_priority_load.setValue(index, Actual_high_priority_load_val);
				}
			}
			return;
		}

		void calculateActual_low_priority_load(int timesteps, float Mop_load_max,  year_TS TS_Pre_Mop_curtailed_Export)
		{
			for (int index = 0; index < timesteps; index++)
			{
				float TS_Pre_Mop_curtailed_Export_val = TS_Pre_Mop_curtailed_Export.getValue(index); // this is a member inside the Grid Object 
				float Actual_low_priority_load_val;
				if (TS_Pre_Mop_curtailed_Export_val > Mop_load_max)
				{
					TS_Actual_low_priority_load.setValue(index, Mop_load_max);
				}
				else
				{
					Actual_low_priority_load_val = TS_Pre_Mop_curtailed_Export_val;
					TS_Actual_low_priority_load.setValue(index, Actual_low_priority_load_val);
				}
			}
			return;
		}

		
		void calculateTS_ESS_aux_load ()
		{
			TS_ESS_aux_load.setallTSvalues(ESS_aux_load); // Subtract timeseries for (small) parasitic load of ESS
		}
		
		void calculateTS_Target_high_load(float Flex_load_max)
		{
		
			TS_Target_high_load.setallTSvalues(Flex_load_max);
		
		}

		void calculateTS_Total_target_load()
		{
			TS_Total_target_load = year_TS::add(TS_Total_fix_load, TS_Target_high_load);

		}

		void calculateTS_Total_load()
		{
			TS_Total_load = year_TS::add(TS_Total_target_load, TS_ESS_aux_load); // Subtract timeseries for (small) parasitic load of ESS

		}

		void calculateTS_ESUM(year_TS TS_RGen_total)
		{
			TS_ESUM = year_TS::subtract(TS_Total_load, TS_RGen_total); // Subtract timeseries for (small) parasitic load of ESS

		}


		//Accessor member functions for TS_year

		year_TS getTS_Fix_load_1() const
		{
			return TS_Fix_load_1;
		}

		year_TS getTS_Fix_load_2() const
		{
			return TS_Fix_load_2;
		}

		year_TS getTS_Total_fix_load() const
		{
			return TS_Total_fix_load;
		}

		year_TS getTS_Actual_high_priority_load() const
		{
			return TS_Actual_high_priority_load;
		}

		year_TS  getTS_Actual_low_priority_load() const
		{
			return TS_Actual_low_priority_load;
		}

		year_TS  getTS_Target_high_load() const
		{
			return TS_Target_high_load;
		}

		year_TS  getTS_Target_mop_load() const
		{
			return TS_Target_mop_load;
		}

		year_TS  getTS_ESS_aux_load() const
		{
			return TS_ESS_aux_load;
		}

		year_TS  getTS_Total_target_load() const
		{
			return TS_Total_target_load;
		}

		year_TS  getTS_Total_load() const
		{
			return TS_Total_load;
		}

		year_TS  getTS_ESUM() const
		{
			return TS_ESUM;
		}

	private:
		year_TS TS_Fix_load_1;
		year_TS TS_Fix_load_2;
		year_TS TS_Total_fix_load;
		year_TS TS_Actual_high_priority_load;
		year_TS TS_Actual_low_priority_load;
		year_TS TS_Target_high_load;
		year_TS TS_Target_mop_load;
		year_TS TS_ESS_aux_load;
		year_TS TS_Total_target_load;
		year_TS TS_Total_load;
		year_TS TS_ESUM;
		float ESS_aux_load;
};

