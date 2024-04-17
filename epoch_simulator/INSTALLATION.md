# Build Instructions
## Building and Running the project (Visual Studio)

1. Run `setup_vcpkg.bat` to configure vcpkg
   
   This script requires administrator privileges.

2. Open the repository as a folder

   The first time this is opened, CMake will run. This may take a couple of minutes.

4. Select the desired project configuration from the dropdown

5. Select `Epoch.exe` from the run dropdown

## Installing Epoch (Visual Studio)

Epoch can be installed from within Visual Studio. This will produce a folder within the `./install` directory containing the executable and all necessary dependencies.

1. Follow the Build steps above to build the project.
  
   IMPORTANT: make sure this is in one of the **release** configurations

2. From the Build dropdown, select `Install Epoch`

## Generating Python Bindings (Visual Studio)

This follows a similar set of steps to building the Epoch executable, with the difference being that there is no target to run as no executable is produced.

1. Select `Python Bindings` from the configuration dropdown

2. Build the project
   
   `Build > Build All` or `Ctrl + Shift + B`

3. Install Epoch
   `Build > Install Epoch`

`epoch_simulator.pyd` and all dependencies can then be found in `./install/python/bin`

This module can then be imported in Python using `import epoch_simulator`. This can either be done inside this installation directory or else it must be added to the path.

## Building without Visual Studio

1. cmake . --preset `<presetName>`

2. cmake --build --preset `<presetName>`

