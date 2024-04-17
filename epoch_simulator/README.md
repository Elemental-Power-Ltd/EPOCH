# EPOCH
Elemental Power Optimiser with Clean Heat

## Building and Running Epoch

Epoch uses CMake and configurations are defined with CMakePresets.json

For detailed instructions, including Visual Studio usage, see [INSTALLATION.md](INSTALLATION.md)


## Project modes

There are currently 3 different modes for EPOCH

### GUI 
Configure the search space through a windows-form based GUI

### Headless
configure the search space through a JSON file

The following Commandline arguments are accepted

`--input`:     specify a path to a directory containing the necessary input data for Epoch

`--output`:    specify a path to a directory to write the output files to

`--config`:    specify a path to a directory containing configuration files for Epoch

`--verbose`:   enable verbose logging

### Python Bindings
Exposes the core Simulator as a Python module
See the [Python Bindings README](epoch_py/README.md) for more information.


## Testing Epoch

See the [Test README](epoch_test/README.md)