from collections.abc import Callable

import numpy as np
import pytest
from numpy.testing import assert_array_almost_equal

from app.internal.utils.conversions import (
    celsius_to_kelvin,
    m3_to_kwh,
    millibar_to_megapascal,
    relative_to_specific_humidity,
)

FloatOrArray = float | np.ndarray


class TestInputFixtures:
    @pytest.fixture
    def float_input(self) -> float:
        return 20.0

    @pytest.fixture
    def array_input(self) -> np.ndarray:
        return np.array([10.0, 20.0, 30.0])

    @pytest.fixture(params=["float_input", "array_input"])
    def float_or_array_input(self, request: pytest.FixtureRequest) -> FloatOrArray:
        return request.getfixturevalue(request.param)


class TestM3ToKWh(TestInputFixtures):
    def test_m3_to_kwh(self, float_or_array_input: FloatOrArray) -> None:
        result = m3_to_kwh(float_or_array_input)  # type: ignore
        expected = float_or_array_input * 38.0 * 1.02264 / 3.6
        assert_array_almost_equal(result, expected)

    def test_m3_to_kwh_custom_calorific_value(self, float_or_array_input: FloatOrArray) -> None:
        calorific_value = 40.0
        result = m3_to_kwh(float_or_array_input, calorific_value)  # type: ignore
        expected = float_or_array_input * calorific_value * 1.02264 / 3.6
        assert_array_almost_equal(result, expected)


class TestCelsiusToKelvin(TestInputFixtures):
    def test_celsius_to_kelvin(self, float_or_array_input: FloatOrArray) -> None:
        result = celsius_to_kelvin(float_or_array_input)  # type: ignore
        expected = float_or_array_input + 273.15
        assert_array_almost_equal(result, expected)

    def test_celsius_to_kelvin_out_of_range(self) -> None:
        with pytest.raises(AssertionError):
            celsius_to_kelvin(-51)
        with pytest.raises(AssertionError):
            celsius_to_kelvin(100)
        with pytest.raises(AssertionError):
            celsius_to_kelvin(np.array([-60, 0, 101]))


class TestMillibarToMegapascal(TestInputFixtures):
    def test_millibar_to_megapascal(self, float_or_array_input: FloatOrArray) -> None:
        input_mbar = 1000 + 9 * (float_or_array_input - 20)  # Ensure input is in valid range
        result = millibar_to_megapascal(input_mbar)  # type: ignore
        expected = input_mbar / 10000
        assert_array_almost_equal(result, expected)

    def test_millibar_to_megapascal_out_of_range(self) -> None:
        with pytest.raises(AssertionError):
            millibar_to_megapascal(799)
        with pytest.raises(AssertionError):
            millibar_to_megapascal(1101)
        with pytest.raises(AssertionError):
            millibar_to_megapascal(np.array([750, 1000, 1200]))


class TestRelativeToSpecificHumidity:
    @pytest.fixture
    def valid_humidity_inputs(self) -> tuple[FloatOrArray, FloatOrArray, FloatOrArray]:
        rel_hum = np.array([0, 50, 100])
        air_temp = np.array([0, 25, 30])
        air_pressure = np.array([1000, 1013, 1020])
        return rel_hum, air_temp, air_pressure

    def test_relative_to_specific_humidity(
        self, valid_humidity_inputs: tuple[FloatOrArray, FloatOrArray, FloatOrArray]
    ) -> None:
        rel_hum, air_temp, air_pressure = valid_humidity_inputs
        result = relative_to_specific_humidity(rel_hum, air_temp, air_pressure)  # type: ignore
        assert isinstance(result, np.ndarray)
        assert isinstance(rel_hum, np.ndarray)
        assert result.shape == rel_hum.shape
        assert np.all(result >= 0)

    def test_relative_to_specific_humidity_out_of_range(self) -> None:
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
    @pytest.mark.parametrize(
        "func",
        [
            m3_to_kwh,
            celsius_to_kelvin,
        ],
    )
    def test_function_with_single_float_and_array(
        self, func: Callable[[FloatOrArray], FloatOrArray], float_input: float, array_input: np.ndarray
    ) -> None:
        float_result = func(float_input)
        array_result = func(array_input)

        assert isinstance(float_result, float | np.ndarray)
        assert isinstance(array_result, np.ndarray)
        assert array_result.shape == array_input.shape
