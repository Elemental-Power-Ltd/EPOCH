"""Test various unit conversion functions."""

# ruff: noqa: D101, D102
from collections.abc import Callable

import numpy as np
import numpy.typing as npt
import pytest
from numpy.testing import assert_array_almost_equal

from app.internal.utils.conversions import (
    celsius_to_kelvin,
    m3_to_kwh,
    millibar_to_megapascal,
    relative_to_specific_humidity,
)

FloatOrArray = float | npt.NDArray[np.floating]


class TestInputFixtures:
    """Fixtures for arrays, floats, or either."""

    @pytest.fixture
    def float_input(self) -> float:
        """Get an example float input."""
        return 20.0

    @pytest.fixture
    def array_input(self) -> npt.NDArray[np.floating]:
        """Get an example array input."""
        return np.array([10.0, 20.0, 30.0])

    @pytest.fixture(params=["float_input", "array_input"])
    def float_or_array_input(self, request: pytest.FixtureRequest) -> float | npt.NDArray[np.floating]:
        """Get a fixture either as a float or as an array."""
        val: float | npt.NDArray[np.floating] = request.getfixturevalue(request.param)
        return val


class TestM3ToKWh(TestInputFixtures):
    """Test that we can convert gas volumes to energy."""

    def test_m3_to_kwh(self, float_or_array_input: float) -> None:
        """Test that we get the right answers for either floats or arrays."""
        result = m3_to_kwh(float_or_array_input)
        expected = float_or_array_input * 38.0 * 1.02264 / 3.6
        assert_array_almost_equal(result, expected)

    def test_m3_to_kwh_custom_calorific_value(self, float_or_array_input: float) -> None:
        """Test that changing the calorific value does what we'd expect."""
        calorific_value = 40.0
        result = m3_to_kwh(float_or_array_input, calorific_value)
        expected = float_or_array_input * calorific_value * 1.02264 / 3.6
        assert_array_almost_equal(result, expected)


class TestCelsiusToKelvin(TestInputFixtures):
    """Temperature conversion tests."""

    def test_celsius_to_kelvin(self, float_or_array_input: float) -> None:
        """Test that converting C to K works like we'd expect."""
        result = celsius_to_kelvin(float_or_array_input)
        expected = float_or_array_input + 273.15
        assert_array_almost_equal(result, expected)

    def test_celsius_to_kelvin_out_of_range(self) -> None:
        """Test that we fail on suspicious inputs."""
        with pytest.raises(AssertionError):
            celsius_to_kelvin(-51)
        with pytest.raises(AssertionError):
            celsius_to_kelvin(100)
        with pytest.raises(AssertionError):
            celsius_to_kelvin(np.array([-60, 0, 101]))


class TestMillibarToMegapascal(TestInputFixtures):
    """Test pressure conversion functions."""

    def test_millibar_to_megapascal(self, float_or_array_input: float) -> None:
        """Test that we get sensible results for some test pressures."""
        input_mbar = 1000 + 9 * (float_or_array_input - 20)  # mangle the inputs into a reasonable range
        result = millibar_to_megapascal(input_mbar)
        expected = input_mbar / 10000
        assert_array_almost_equal(result, expected)

    def test_millibar_to_megapascal_out_of_range(self) -> None:
        """Test the suspicious range checks (should all be standard for Earth)."""
        with pytest.raises(AssertionError):
            millibar_to_megapascal(799)
        with pytest.raises(AssertionError):
            millibar_to_megapascal(1101)
        with pytest.raises(AssertionError):
            millibar_to_megapascal(np.array([750, 1000, 1200]))


class TestRelativeToSpecificHumidity:
    """Test humidity conversion functions."""

    @pytest.fixture
    def valid_humidity_inputs(self) -> tuple[npt.NDArray[np.floating], npt.NDArray[np.floating], npt.NDArray[np.floating]]:
        """Get some reasonable physical inputs."""
        rel_hum = np.array([0, 50, 100])
        air_temp = np.array([0, 25, 30])
        air_pressure = np.array([1000, 1013, 1020])
        return rel_hum, air_temp, air_pressure

    def test_relative_to_specific_humidity(
        self, valid_humidity_inputs: tuple[npt.NDArray[np.floating], npt.NDArray[np.floating], npt.NDArray[np.floating]]
    ) -> None:
        """Test that those inputs give the right shape results."""
        rel_hum, air_temp, air_pressure = valid_humidity_inputs
        result = relative_to_specific_humidity(rel_hum, air_temp, air_pressure)
        assert isinstance(result, np.ndarray)
        assert isinstance(rel_hum, np.ndarray)
        assert result.shape == rel_hum.shape
        assert np.all(result >= 0)

    def test_relative_to_specific_humidity_out_of_range(self) -> None:
        """Test that suspicious inputs fail."""
        with pytest.raises(AssertionError):
            relative_to_specific_humidity(-1, 25, 1013)
        with pytest.raises(AssertionError):
            relative_to_specific_humidity(101, 25, 1013)
        with pytest.raises(AssertionError):
            relative_to_specific_humidity(50, -51, 1013)
        with pytest.raises(AssertionError):
            relative_to_specific_humidity(50, 100, 1013)
        with pytest.raises(AssertionError):
            relative_to_specific_humidity(50, 25, 899)
        with pytest.raises(AssertionError):
            relative_to_specific_humidity(50, 25, 1101)


class TestGeneralFunctionality(TestInputFixtures):
    """Test thtat the functions work with floats or arrays."""

    @pytest.mark.parametrize(
        "func",
        [
            m3_to_kwh,
            celsius_to_kelvin,
        ],
    )
    def test_function_with_single_float_and_array(
        self, func: Callable[[FloatOrArray], FloatOrArray], float_input: float, array_input: npt.NDArray[np.floating]
    ) -> None:
        """Test each function with a float and an array, and make sure they're sane."""
        float_result = func(float_input)
        array_result = func(array_input)

        assert isinstance(float_result, float)
        assert isinstance(array_result, np.ndarray)
        assert array_result.shape == array_input.shape
