#pragma once
struct InputValues {
	float years; float days; float hours; float timestep_minutes; float timestep_hours; float timewindow;
	float Fixed_load1_scalar_lower; float Fixed_load1_scalar_upper; float Fixed_load1_scalar_step;
	float Fixed_load2_scalar_lower; float Fixed_load2_scalar_upper; float Fixed_load2_scalar_step;
	float Flex_load_max_lower; float Flex_load_max_upper; float Flex_load_max_step;
	float Mop_load_max_lower; float Mop_load_max_upper; float Mop_load_max_step;
	float ScalarRG1_lower; float ScalarRG1_upper; float ScalarRG1_step;
	float ScalarRG2_lower; float ScalarRG2_upper; float ScalarRG2_step;
	float ScalarRG3_lower; float ScalarRG3_upper; float ScalarRG3_step;
	float ScalarRG4_lower; float ScalarRG4_upper; float ScalarRG4_step;
	float ScalarHL1_lower; float ScalarHL1_upper; float ScalarHL1_step;
	float ScalarHYield1_lower; float ScalarHYield1_upper; float ScalarHYield1_step;
	float ScalarHYield2_lower; float ScalarHYield2_upper; float ScalarHYield2_step;
	float ScalarHYield3_lower; float ScalarHYield3_upper; float ScalarHYield3_step;
	float ScalarHYield4_lower; float ScalarHYield4_upper; float ScalarHYield4_step;
	float GridImport_lower; float GridImport_upper; float GridImport_step;
	float GridExport_lower; float GridExport_upper; float GridExport_step;
	float Import_headroom_lower; float Import_headroom_upper; float Import_headroom_step;
	float Export_headroom_lower; float Export_headroom_upper; float Export_headroom_step;
	float ESS_charge_power_lower; float ESS_charge_power_upper; float ESS_charge_power_step;
	float ESS_discharge_power_lower; float ESS_discharge_power_upper; float ESS_discharge_power_step;
	float ESS_capacity_lower; float ESS_capacity_upper; float ESS_capacity_step;
	float ESS_RTE_lower; float ESS_RTE_upper; float ESS_RTE_step;
	float ESS_aux_load_lower; float ESS_aux_load_upper; float ESS_aux_step;
	float ESS_start_SoC_lower; float ESS_start_SoC_upper; float ESS_start_SoC_step;
	int ESS_charge_mode_lower; int ESS_charge_mode_upper;
	int ESS_discharge_mode_lower; int ESS_discharge_mode_upper;
};