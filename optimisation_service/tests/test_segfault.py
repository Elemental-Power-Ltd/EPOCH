from epoch_simulator import TaskData, Simulator
import os
import pathlib


def test_bad_taskdata():
    taskdata_values = {
        "OPEX_limit": 0,
        "time_budget_min": 0,
        "ScalarRG4": 0.707456,
        "ScalarRG2": 0.76290596,
        "ScalarRG1": 0.5254643,
        "ESS_capacity": 0.16909198,
        "Fixed_load2_scalar": 0.62250096,
        "ScalarHYield": 0.9997197,
        "Mop_load_max": 0.7894141,
        "Flex_load_max": 0.05282427,
        "CAPEX_limit": 0,
        "Export_headroom": 0.23178641,
        "Export_kWh_price": 0,
        "EV_flex": 0.22536692,
        "ScalarHL1": 0.23298134,
        "timestep_hours": 0,
        "timewindow": 8760,
        "ASHP_HPower": 0.96678114,
        "ASHP_HotTemp": 0.8829448,
        "ASHP_RadTemp": 0.51420677,
        "GridImport": 0.51393175,
        "Fixed_load1_scalar": 0.09267972,
        "GridExport": 0.564019,
        "Import_headroom": 0.69443095,
        "Min_power_factor": 0.47727498,
        "ESS_discharge_power": 0.14595999,
        "ScalarRG3": 0.9346839,
        "ESS_charge_power": 0.5173513,
        "ESS_start_SoC": 0.6106042,
        "ESS_discharge_mode": 0,
        "ESS_charge_mode": 0,
        "target_max_concurrency": 0,
        "ASHP_HSource": 0,
        "u150_EV_CP_number": 0,
        "r50_EV_CP_number": 0,
        "f22_EV_CP_number": 0,
        "s7_EV_CP_number": 0,
    }

    # taskdata_values["timestep_hours"] = 1.0
    taskdata_values["timestep_hours"] = 2.0
    td = TaskData()
    for key, val in taskdata_values.items():
        setattr(td, key, val)

    input_dir = pathlib.Path(".") / "Epoch" / "InputData"
    sim = Simulator(inputDir=str(input_dir))
    sim.simulate_scenario(td)
