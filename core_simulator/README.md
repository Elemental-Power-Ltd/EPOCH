# EPOCH
Elemental Power Optimiser with Clean Heat

This is the Core Simulator, written in C++ and exposed as python bindings.

## Building and Running Epoch

Epoch uses CMake and configurations are defined with CMakePresets.json

For detailed instructions, including Visual Studio usage, see [INSTALLATION.md](INSTALLATION.md)


### Headless

The pure C++ version of EPOCH runs headlessly.

##### Input Data

Epoch expects to find three input files within the same input directory
- `taskData.json` to define the site components for this simulation
- `siteData.json` to define the characteristics of the site (energy demands, solar potential, air temperature etc...)
- `epochConfig.json` for general configuration

By default, EPOCH expexts these will be in `./InputData`

#### Output Data

Epoch writes some results to file. By default, these are written to `./OutputData`

##### Operation

Use `-h` for the full set of options

```
Usage: Epoch [--help] [--version] [--input VAR] [--output VAR] [--verbose] [[--json]|[--human]]

Optional arguments:
  -h, --help     shows help message and exits
  -v, --version  prints version information and exits
  -i, --input    The directory containing all input files [nargs=0..1] [default: "./InputData"]
  -o, --output   The directory to write all output files to [nargs=0..1] [default: "./OutputData"]
  --verbose      Set logging to verbose
  -J, --json     Output JSON to stdout. Automatically quiets all logs
  -H, --human    Output a human readable summary
```

The JSON and Human-readable modes are mutually exclusive, defaulting to human-readable.

### Python Bindings
Exposes the core Simulator as a Python module
See the [Python Bindings README](epoch_py/README.md) for more information.


## Testing Epoch

See the [Test README](epoch_test/README.md)
