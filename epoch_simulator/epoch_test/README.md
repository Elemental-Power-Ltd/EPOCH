# Epoch Tests

These tests use Gtest. There is currently a single test to check that the outputs match against known results

## Visual Studio integration

Tests can be run in two ways within visual studio.

1. Select `Epoch_test.exe` from the target dropdown for a given configuration and run it in the console.

    The working directory and any arguments can be configured by `launch.vs.json`

2. Open the test explorer

    The working directory is determind by the argument supplied to `gtest_discover_tests` within CMakeLists.txt