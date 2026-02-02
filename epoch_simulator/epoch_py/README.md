# Epoch Python Bindings

This directory contains the Python Bindings that expose the core Simulator as a Python module using PyBind11.

## Building the Python Bindings

See details in the top-level [Installation](../INSTALLATION.md#generating-python-bindings-visual-studio) document.

## Using the Python Bindings

```Python
import epoch_simulator as eps

print(eps.__version__)

# Create a simulator and task
sim = eps.Simulator.from_file("./InputData/siteData.json", "./InputData/epochConfig.json")
task = eps.TaskData()

# Add some components to the task
task.building = eps.Building()
task.energy_storage_system = eps.EnergyStorageSystem()
task.grid = eps.Grid()

for charge_power in range(300, 600, 100):
  task.energy_storage_system.charge_power = charge_power

  for discharge_power in range(300, 600, 100):
    task.energy_storage_system.discharge_power = discharge_power

    result = sim.simulate_scenario(task)
    print(result)

```


#### TaskData

The TaskData contains the input parameters necessary to run a simulation.

`TaskData()`

A default TaskData contains no components. Components can be added by creating an instance of the relevant type.

This class implements the `__repr__` method so the print method can be used to see the full state.

TaskData also contains a static `from_json` method to create an instance from a json string.

#### Simulator

`Simulator()`

Simulators can be instantiated via one of two factory methods:
- `sim = Simulator.from_json(site_data_json_str, config_json_str)`
- `sim = Simulator.from_file(site_data_filepath, config_filepath_)`

Both methods accept SiteData and a config represented as json; as a json string or a path to siteData.json respectively.

`simulate_scenario(task)`

Run a scenario, returning a `Result` object

`is_valid(task)`

Check if the SiteData / TaskData pairing is valid without running a simulation

`calculate_capex(task)`

Calculate the capex for a site defined by its SiteData / TaskData pair

#### Result

A  `SimulationResult` is returned by calls to `simulate_scenario`. It contains the result values for each of the five objectives.

This class implements the `__repr__` method so the print method can be used to see the state.

#### Report Data

When the `simulate_scenario` function is called, setting the flag `fullReporting=True` will return the full time series within the `report_data` field.

When `fullReporting` is False (default behaviour) the `report_data` will be set to `None`


```Python
...
>> result = sim.simulate_scenario(task, fullReporting=True)
>> assert(result.report_data is not None)
>> result.report_data.Actual_import_shortfall
array([ 0.      ,  0.      ,  0.      , ..., 19.077652,  7.701477,
        7.701477], dtype=float32)
```

