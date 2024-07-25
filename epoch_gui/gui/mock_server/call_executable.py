# Copied from the python_wrapper repo to get something working

import json
import os
import subprocess

# when running this file directly, adjust this to point to a version of Epoch
PATH_TO_PROJECT = "..\\Epoch"


def main():
    # this main method provides an example of how to use these functions

    print("########## Start executable ##########")
    results = run_headless(PATH_TO_PROJECT,
                           "Data/InputData", "Data/OutputData")
    print("########### End executable ###########")

    print(results)


def run_headless(project_path, input_dir=None, output_dir=None, config_dir=None):
    """
    Run the headless version of Epoch as a subprocess
    :param project_path: The path to the root of the Epoch repository
    :param input_dir: A directory containing input data for Epoch. Defaults to $project_path$/InputData
    :param output_dir: The directory to write the output to. Defaults to ./Data/OutputData
    :param config_dir: A directory containing the config file(s) for Epoch. Defaults to $project_path$/Config
    :return: A dictionary containing the best value for each of the five objectives
    """
    exe_name = "Epoch.exe"

    path_to_build = _get_full_path_to_build(project_path)
    full_path_to_exe = os.path.join(path_to_build, exe_name)
    assert os.path.isfile(full_path_to_exe)

    # input_dir, output_dir and config_dir can all be None
    # in which case we default to the following:
    #   input_dir   - the InputData directory in the Epoch root directory
    #   output_dir  - Data/OutputData within this project
    #   config_dir  - the Config directory in the Epoch root directory

    if input_dir is None:
        input_dir = os.path.join(project_path, "InputData")

    if output_dir is None:
        output_dir = "Data/OutputData"

    if config_dir is None:
        config_dir = os.path.join(project_path, "Config")

    # check these directories exist
    assert os.path.isdir(input_dir)
    assert os.path.isdir(output_dir)
    assert os.path.isdir(config_dir)

    # check for required files within the directories
    assert os.path.isfile(os.path.join(input_dir, "inputParameters.json"))
    assert os.path.isfile(os.path.join(config_dir, "EpochConfig.json"))

    result = subprocess.run([full_path_to_exe,
                             "--input", input_dir, "--output", output_dir, "--config", config_dir])

    assert result.returncode == 0

    output_json = os.path.join(output_dir, "outputParameters.json")

    with open(output_json, 'r') as f:
        full_output = json.load(f)

    minimal_output = {
        "annualised": full_output["annualised"],
        "scenario_cost_balance": full_output["scenario_cost_balance"],
        "scenario_carbon_balance": full_output["scenario_carbon_balance"],
        "payback_horizon": full_output["payback_horizon"],
        "CAPEX": full_output["CAPEX"],

        "time_taken": full_output["time_taken"]
    }

    return minimal_output


def _get_full_path_to_build(project_path):
    path_to_build = "install\\headless\\bin"
    return os.path.join(project_path, path_to_build)


if __name__ == "__main__":
    main()
