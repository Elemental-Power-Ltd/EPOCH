#pragma once
class Hload
{
	public:
		Hload(year_TS TS_Heatload = {}, year_TS TS_Heat_shortfall = {}, year_TS TS_Heat_surplus = {},
			year_TS TS_Scaled_electrical_fix_heat_load_1 = {}, year_TS TS_Scaled_electrical_fix_heat_load_2 = {},
			year_TS TS_Scaled_electrical_highflex_heat_load = {}, year_TS TS_Scaled_electrical_lowflex_heat_load = {},
			year_TS TS_Electrical_load_scaled_heat_yield = {})
		: TS_Heatload(TS_Heatload), TS_Heat_shortfall(TS_Heat_shortfall), TS_Heat_surplus(TS_Heat_surplus),
		  TS_Scaled_electrical_fix_heat_load_1(TS_Scaled_electrical_fix_heat_load_1), TS_Scaled_electrical_fix_heat_load_2(TS_Scaled_electrical_fix_heat_load_2),
		  TS_Scaled_electrical_highflex_heat_load(TS_Scaled_electrical_highflex_heat_load), TS_Scaled_electrical_lowflex_heat_load(TS_Scaled_electrical_lowflex_heat_load),
		  TS_Electrical_load_scaled_heat_yield(TS_Electrical_load_scaled_heat_yield)
		 {}


		void writeTS_Heatload(std::vector<float> new_data)
		{
			
			TS_Heatload.setTSvalues(new_data);
			return;
		}

		void writeTS_Scaled_electrical_fix_heat_load_1(std::vector<float> new_data)
		{

			TS_Scaled_electrical_fix_heat_load_1.setTSvalues(new_data);
			return;
		}

		void writeTS_Scaled_electrical_fix_heat_load_2(std::vector<float> new_data)
		{

			TS_Scaled_electrical_fix_heat_load_2.setTSvalues(new_data);
			return;
		}

		void scaleTS_Scaled_electrical_fix_heat_load_1(float scalar)
		{

			TS_Scaled_electrical_fix_heat_load_1.scaleTSvalues(scalar);
			return;
		}

		void scaleTS_Scaled_electrical_fix_heat_load_2(float scalar)
		{

			TS_Scaled_electrical_fix_heat_load_2.scaleTSvalues(scalar);;
			return;
		}

		void calculateElectrical_load_scaled_heat_yield(year_TS TS_Actual_high_priority_load, year_TS TS_Actual_low_priority_load, float ScalarHYield3, float ScalarHYield4)
		{
			TS_Actual_high_priority_load.scaleTSvalues(ScalarHYield3);
			TS_Actual_low_priority_load.scaleTSvalues(ScalarHYield4);
			TS_Electrical_load_scaled_heat_yield.addto(TS_Scaled_electrical_fix_heat_load_1);
			TS_Electrical_load_scaled_heat_yield.addto(TS_Scaled_electrical_fix_heat_load_2);
			TS_Electrical_load_scaled_heat_yield.addto(TS_Actual_high_priority_load);
			TS_Electrical_load_scaled_heat_yield.addto(TS_Actual_low_priority_load);
			return;
		}

		void calculateHeat_shortfall(int timesteps)
		{
			for (int index = 0; index < timesteps; index++)
			{
				float TS_Heat_shortfall_val;
				float TS_Heat_load_val = TS_Heatload.getValue(index); // this is a member inside the Grid Object 
				float TS_Electrical_scaled_heat_load_val = TS_Electrical_load_scaled_heat_yield.getValue(index);
				if (TS_Heat_load_val > TS_Electrical_scaled_heat_load_val)
				{
					TS_Heat_shortfall_val = TS_Heat_load_val - TS_Electrical_scaled_heat_load_val;
					TS_Heat_shortfall.setValue(index, TS_Heat_shortfall_val);
				}
				else
				{
					TS_Heat_shortfall.setValue(index, 0);
				}
			}
			return;
		}

		void calculateHeat_surplus(int timesteps)
		{
			for (int index = 0; index < timesteps; index++)
			{
				float TS_Heat_surplus_val;
				float TS_Heat_load_val = TS_Heatload.getValue(index); // this is a member inside the Grid Object 
				float TS_Electrical_scaled_heat_load_val = TS_Electrical_load_scaled_heat_yield.getValue(index);
				if (TS_Heat_load_val < TS_Electrical_scaled_heat_load_val)
				{
					TS_Heat_surplus_val = TS_Electrical_scaled_heat_load_val - TS_Heat_load_val;
					TS_Heat_surplus.setValue(index, TS_Heat_surplus_val);
				}
				else
				{
					TS_Heat_surplus.setValue(index, 0);
				}
			}
			return;
		}

		
		//Accessor member functions for TS_year
		year_TS getTS_Heatload()
		{
			return TS_Heatload;
		}

		year_TS getTS_Heat_shortfall() const
		{
			return TS_Heat_shortfall;
		}

		year_TS  getTS_Heat_surplus() const
		{
			return TS_Heat_surplus;
		}

		year_TS  getTS_Scaled_electrical_fix_heat_load_1()
		{
			return TS_Scaled_electrical_fix_heat_load_1;
		}

		year_TS  getTS_Scaled_electrical_fix_heat_load_2()
		{
			return TS_Scaled_electrical_fix_heat_load_2;
		}

		year_TS  getTS_Scaled_electrical_highflex_heat_load()
		{
			return TS_Scaled_electrical_highflex_heat_load;
		}

		year_TS  getTS_Scaled_electrical_lowflex_heat_load()
		{
			return TS_Scaled_electrical_lowflex_heat_load;
		}

		year_TS  getTS_Electrical_load_scaled_heat_yield()
		{
			return TS_Electrical_load_scaled_heat_yield;
		}


	private:
	year_TS TS_Heatload;
	year_TS TS_Heat_shortfall;
	year_TS TS_Heat_surplus;
	year_TS TS_Scaled_electrical_fix_heat_load_1; 
	year_TS TS_Scaled_electrical_fix_heat_load_2; 
	year_TS TS_Scaled_electrical_highflex_heat_load;
	year_TS TS_Scaled_electrical_lowflex_heat_load;
	year_TS TS_Electrical_load_scaled_heat_yield;
};

