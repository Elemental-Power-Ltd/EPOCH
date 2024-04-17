# Epoch Python Bindings

This directory contains the Python Bindings that expose the core Simulator as a Python module using PyBind11.

## Building the Python Bindings

See details in the top-level [Installation](../INSTALLATION.md#generating-python-bindings-visual-studio) document.

## Using the Python Bindings

```Python
import epoch_simulator as eps

conf = eps.Config()
sim = eps.Simulator()

for charge_power in range(300, 600, 100):
  conf.ESS_charge_power = charge_power

  for discharge_power in range(300, 600, 100):
    conf.ESS_discharge_power = discharge_power

    result = sim.simulate_scenario(conf)
    print(result)

```

The bindings expose 3 classes:

#### Config

The Config contains the input parameters necessary to run a simulation.

`Config()`

 Upon instantiation, all of the fields are set to default values - these can be changed as desired.

This class implements the `__repr__` method so the print method can be used to see the full state.

#### Simulator

`Simulator()`

Instantiating a Simulator will create a Simulator object that loads in the necessary historical data from a directory called InputData in the current working directory.

`simulate_scenario(config)`

Run a scenario, returning a `Result` object

#### Result

The result class is returned by calls to `simulate_scenario`. It contains the result values for each of the five objectives.

This class implements the `__repr__` method so the print method can be used to see the state.
