from pathlib import Path

import pytest

try:
    from epoch_simulator import Simulator, TaskData

    from app.internal.task_data_wrapper import PySimulationResult, PyTaskData

    HAS_TRUE = True
except ImportError:
    HAS_EPOCH = False


@pytest.mark.requires_epoch
class TestEpochIntegration:
    def test_epoch_still_runs_default(self) -> None:
        """
        Test that we can run Epoch with a PyTaskData and get the same result.
        """
        old_td = TaskData()
        new_td = PyTaskData()
        sim = Simulator(inputDir=str(Path("tests", "data", "benchmarks", "var-3", "InputData")))

        old_res = PySimulationResult(sim.simulate_scenario(old_td))
        new_res = PySimulationResult(sim.simulate_scenario(new_td))

        assert new_res == old_res

    def test_epoch_still_runs_changed(self) -> None:
        """
        Test that we can run Epoch with a changed PyTaskData and get the same result.
        """
        old_td = TaskData()
        new_td = PyTaskData()

        old_td.ESS_capacity += 10
        new_td["ESS_capacity"] += 10
        sim = Simulator(inputDir=str(Path("tests", "data", "benchmarks", "var-3", "InputData")))

        old_res = PySimulationResult(sim.simulate_scenario(old_td))
        new_res = PySimulationResult(sim.simulate_scenario(new_td))

        assert new_res == old_res


@pytest.mark.requires_epoch
class TestPyTaskDataWrapped:
    def test_kwargs_works(self) -> None:
        """Test that the kwarg setter works"""
        td = PyTaskData(CAPEX_limit=3142)
        assert td["CAPEX_limit"] == 3142
        assert td.CAPEX_limit == 3142

    def test_can_get_attributes(self) -> None:
        """
        Test that we can get attributes from a taskdata like a dict
        """
        td = PyTaskData()
        for key in td._VALID_KEYS:
            assert td[key] is not None

    def test_cant_get_bad_attributes(self) -> None:
        """
        Test that we can't get bad attributes
        """
        td = PyTaskData()
        for key in ["foo", "bar", "quux"]:
            with pytest.raises(KeyError):
                td[key]

    def test_can_set_attributes(self) -> None:
        """
        Test that we can set attributes and mutate them
        """
        td = PyTaskData()
        for key in td._VALID_KEYS:
            td[key] = 10
            # note that python uses doubles and C++ uses floats, so only approx equality
            assert td[key] == pytest.approx(10)

        for key in td._VALID_KEYS:
            td[key] += 10
            # note that python uses doubles and C++ uses floats, so only approx equality
            assert td[key] == pytest.approx(20)

    def test_cant_set_bad_attributes(self) -> None:
        """
        Test that we can't accidentally set bad attributes that C++ will ignore
        """
        td = PyTaskData()
        for key in ["foo", "bar", "quux"]:
            with pytest.raises(KeyError):
                td[key] = 10

    def test_dunder_methods(self) -> None:
        """
        Test that the keys, values and items iterators work
        """
        td = PyTaskData()
        for raw_key, raw_value, (key, value) in zip(td.keys(), td.values(), td.items()):
            assert raw_key == key
            assert raw_value == value

    def test_contains(self) -> None:
        """
        Test that we can look up keys in a PyTaskData
        """
        td = PyTaskData()
        assert "CAPEX_limit" in td
        assert "foo" not in td
