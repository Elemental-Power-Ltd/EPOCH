# EPOCH
Elemental Power Optimiser with Clean Heat

## Building and Running Epoch

Epoch uses CMake and configurations are defined with CMakePresets.json

For detailed instructions, including Visual Studio usage, see [INSTALLATION.md](INSTALLATION.md)


## Project modes

There are currently 2 different modes for EPOCH

### Headless
configure the search space through a JSON file

The following Commandline arguments are accepted

##### Filepaths

`--input`:     specify a path to a directory containing the necessary input data for Epoch

`--output`:    specify a path to a directory to write the output files to

`--config`:    specify a path to a directory containing configuration files for Epoch

##### Operation

`-sim` / `--simulation`:        run a single simulation, as defined by `taskData.json`

`-opt` / `--optimisation`:        run optimisation over a search space defined in `inputParameters.json`

If neither mode is specified, you will be prompted to select interactively with the keyboard.

##### Other

`--verbose`:   enable verbose logging

### Python Bindings
Exposes the core Simulator as a Python module
See the [Python Bindings README](epoch_py/README.md) for more information.


## Testing Epoch

See the [Test README](epoch_test/README.md)