from pathlib import Path

import pytest

from app.internal.epl_typing import ConstraintDict, ParameterDict
from app.internal.problem import Problem, load_problem


@pytest.fixture
def empty_constraints() -> ConstraintDict:
    return {
        "annualised_cost": [None, None],
        "capex": [None, None],
        "carbon_balance": [None, None],
        "cost_balance": [None, None],
        "payback_horizon": [None, None],
    }


@pytest.fixture
def default_parameters() -> ParameterDict:
    return {
        "ASHP_HPower": [70.0, 70.0, 0.0],
        "ASHP_HSource": [1, 1, 0],
        "ASHP_HotTemp": [43.0, 43.0, 0.0],
        "ASHP_RadTemp": [70.0, 70.0, 0.0],
        "CAPEX_limit": 500.0,
        "ESS_capacity": [0, 1000, 100],
        "ESS_charge_mode": [1, 1, 0],
        "ESS_charge_power": [300, 600, 50],
        "ESS_discharge_mode": [1, 1, 0],
        "ESS_discharge_power": [400, 800, 50],
        "ESS_start_SoC": [0.5, 0.5, 0],
        "EV_flex": [0.5, 0.5, 0.0],
        "Export_headroom": [0, 0, 0],
        "Fixed_load1_scalar": [1, 1, 0],
        "Fixed_load2_scalar": [3, 3, 0],
        "Flex_load_max": [50, 50, 0],
        "GridExport": [95, 95, 0],
        "GridImport": [95, 95, 0],
        "Import_headroom": [0, 0, 0],
        "Min_power_factor": [0.95, 0.95, 0.0],
        "Mop_load_max": [300, 300, 0],
        "OPEX_limit": 20.0,
        "ScalarHL1": [1, 1, 0],
        "ScalarHYield": [0.75, 0.75, 0.0],
        "ScalarRG1": [600, 600, 0],
        "ScalarRG2": [100, 100, 0],
        "ScalarRG3": [50, 50, 0],
        "ScalarRG4": [0, 0, 0],
        "Export_kWh_price": 5.0,
        "f22_EV_CP_number": [3, 3, 0],
        "r50_EV_CP_number": [0, 0, 0],
        "s7_EV_CP_number": [0, 0, 0],
        "target_max_concurrency": 44,
        "time_budget_min": 1.0,
        "timestep_hours": 1.0,
        "u150_EV_CP_number": [0, 0, 0],
    }


class TestProblem:
    def test_good_inputs(
        self, empty_constraints: ConstraintDict, default_parameters: ParameterDict
    ) -> None:
        """
        Test that the problem class works with valid input.
        """
        name = "test"
        objectives = {"carbon_balance": -1}
        constraints = empty_constraints
        parameters = default_parameters
        input_dir = Path("data", "test_benchmark", "InputData")

        Problem(name, objectives, constraints, parameters, input_dir)

    def test_bad_objective_names(
        self, empty_constraints: ConstraintDict, default_parameters: ParameterDict
    ) -> None:
        """
        Test that we can't set bad objective names.
        """
        name = "test"
        constraints = empty_constraints
        parameters = default_parameters
        input_dir = Path("data", "test_benchmark", "InputData")

        objectives = {"amazingness": -1}
        with pytest.raises(ValueError):
            Problem(name, objectives, constraints, parameters, input_dir)

    def test_bad_objective_values(
        self, empty_constraints: ConstraintDict, default_parameters: ParameterDict
    ) -> None:
        """
        Test that we can't set bad objective values.
        """
        name = "test"
        constraints = empty_constraints
        parameters = default_parameters
        input_dir = Path("data", "test_benchmark", "InputData")

        objectives = {"carbon_balance": 0.5}
        with pytest.raises(ValueError):
            Problem(name, objectives, constraints, parameters, input_dir)  # type: ignore

    def test_missing_constraint(self, default_parameters: ParameterDict) -> None:
        """
        Test that we can't set constraints with missing objectives.
        """
        name = "test"
        objectives = {"carbon_balance": -1}
        parameters = default_parameters
        input_dir = Path("data", "test_benchmark", "InputData")

        constraints = {
            "annualised_cost": (None, None),
            "capex": (None, None),
            "carbon_balance": (None, None),
            "cost_balance": (None, None),
        }
        with pytest.raises(ValueError):
            Problem(name, objectives, constraints, parameters, input_dir)

    def test_bad_constraint_names(self, default_parameters: ParameterDict) -> None:
        """
        Test that we can't set constraints with bad objective names.
        """
        name = "test"
        objectives = {"carbon_balance": -1}
        parameters = default_parameters
        input_dir = Path("data", "test_benchmark", "InputData")
        constraints = {
            "a": (None, None),
            "b": (None, None),
            "c": (None, None),
            "d": (None, None),
            "e": (None, None),
        }
        with pytest.raises(ValueError):
            Problem(name, objectives, constraints, parameters, input_dir)

    def test_bad_constraint_bounds(
        self, empty_constraints: ConstraintDict, default_parameters: ParameterDict
    ) -> None:
        """
        Test that we can't set bad constraint bounds, lower bound greater than upper bound.
        """
        name = "test"
        objectives = {"carbon_balance": -1}
        parameters = default_parameters
        input_dir = Path("data", "test_benchmark", "InputData")
        constraints = empty_constraints
        constraints["annualised_cost"] = (100.0, 1.0)  # type: ignore

        with pytest.raises(ValueError):
            Problem(name, objectives, constraints, parameters, input_dir)

    def test_bad_parameter_bounds(
        self, empty_constraints: ConstraintDict, default_parameters: ParameterDict
    ) -> None:
        """
        Test that we can't set bad parameter bounds, lower bound greater than upper bound.
        """
        name = "test"
        objectives = {"carbon_balance": -1}
        constraints = empty_constraints
        input_dir = Path("data", "test_benchmark", "InputData")
        parameters = default_parameters
        parameters["ASHP_HPower"] = [80.0, 70.0, 1.0]  # bad bounds

        with pytest.raises(ValueError):
            Problem(name, objectives, constraints, parameters, input_dir)

    def test_bad_parameter_stepsize(
        self, empty_constraints: ConstraintDict, default_parameters: ParameterDict
    ) -> None:
        """
        Test that we can't set bad parameter stepsize.
        """
        name = "test"
        objectives = {"carbon_balance": -1}
        constraints = empty_constraints
        input_dir = Path("data", "test_benchmark", "InputData")
        parameters = default_parameters
        parameters["ASHP_HPower"] = [60.0, 70.0, 0.0]

        with pytest.raises(ValueError):
            Problem(name, objectives, constraints, parameters, input_dir)

    def test_variable_parameters(
        self, empty_constraints: ConstraintDict, default_parameters: ParameterDict
    ) -> None:
        """
        Test that the ss_variables method returns the correct search space variables.
        """
        name = "test"
        objectives = {"carbon_balance": -1}
        constraints = empty_constraints
        parameters = default_parameters
        input_dir = Path("data", "test_benchmark", "InputData")

        problem = Problem(name, objectives, constraints, parameters, input_dir)
        assert problem.variable_param() == {
            "ESS_capacity": [0, 1000, 100],
            "ESS_charge_power": [300, 600, 50],
            "ESS_discharge_power": [400, 800, 50],
        }

    def test_constant_parameters(
        self, empty_constraints: ConstraintDict, default_parameters: ParameterDict
    ) -> None:
        """
        Test that the ss_constants method returns the correct search space constants.
        """
        name = "test"
        objectives = {"carbon_balance": -1}
        constraints = empty_constraints
        parameters = default_parameters
        input_dir = Path("data", "test_benchmark", "InputData")

        problem = Problem(name, objectives, constraints, parameters, input_dir)
        assert problem.constant_param() == {
            "ASHP_HPower": 70.0,
            "ASHP_HSource": 1,
            "ASHP_HotTemp": 43.0,
            "ASHP_RadTemp": 70.0,
            "CAPEX_limit": 500.0,
            "ESS_charge_mode": 1,
            "ESS_discharge_mode": 1,
            "ESS_start_SoC": 0.5,
            "EV_flex": 0.5,
            "Export_headroom": 0,
            "Fixed_load1_scalar": 1,
            "Fixed_load2_scalar": 3,
            "Flex_load_max": 50,
            "GridExport": 95,
            "GridImport": 95,
            "Import_headroom": 0,
            "Min_power_factor": 0.95,
            "Mop_load_max": 300,
            "OPEX_limit": 20.0,
            "ScalarHL1": 1,
            "ScalarHYield": 0.75,
            "ScalarRG1": 600,
            "ScalarRG2": 100,
            "ScalarRG3": 50,
            "ScalarRG4": 0,
            "Export_kWh_price": 5.0,
            "f22_EV_CP_number": 3,
            "r50_EV_CP_number": 0,
            "s7_EV_CP_number": 0,
            "target_max_concurrency": 44,
            "time_budget_min": 1.0,
            "timestep_hours": 1.0,
            "u150_EV_CP_number": 0,
        }

    def test_size(
        self, empty_constraints: ConstraintDict, default_parameters: ParameterDict
    ) -> None:
        """
        Test that the ss_size method returns the correct search space size.
        """
        name = "test"
        objectives = {"carbon_balance": -1}
        constraints = empty_constraints
        parameters = default_parameters
        input_dir = Path("data", "test_benchmark", "InputData")

        problem = Problem(name, objectives, constraints, parameters, input_dir)
        assert problem.size() == 11 * 7 * 9

    def test_split_objectives(
        self, empty_constraints: ConstraintDict, default_parameters: ParameterDict
    ) -> None:
        name = "test"
        objectives = {"carbon_balance": -1, "capex": 1}
        constraints = empty_constraints
        parameters = default_parameters
        input_dir = Path("data", "test_benchmark", "InputData")

        problem = Problem(name, objectives, constraints, parameters, input_dir)
        problem_a = Problem(
            name, {"carbon_balance": -1}, constraints, parameters, input_dir
        )
        problem_b = Problem(name, {"capex": 1}, constraints, parameters, input_dir)

        assert list(problem.split_objectives()) == [problem_a, problem_b]


class TestProblemLoading:
    def test_load_problem(self, empty_constraints: ConstraintDict) -> None:
        name = "var-3"
        problem_dir = Path("tests", "data", "benchmarks")
        problem = load_problem(name, problem_dir)

        assert problem.name == "var-3"
        assert problem.objectives == {
            "carbon_balance": -1,
            "cost_balance": -1,
            "capex": 1,
            "payback_horizon": 1,
            "annualised_cost": 1,
        }
        assert problem.constraints == empty_constraints
        assert problem.parameters == {
            "ASHP_HPower": [70.0, 70.0, 0.0],
            "ASHP_HSource": [1, 1, 0],
            "ASHP_HotTemp": [43.0, 43.0, 0.0],
            "ASHP_RadTemp": [70.0, 70.0, 0.0],
            "CAPEX_limit": 500.0,
            "ESS_capacity": [0, 1000, 100],
            "ESS_charge_mode": [1, 1, 0],
            "ESS_charge_power": [300, 600, 50],
            "ESS_discharge_mode": [1, 1, 0],
            "ESS_discharge_power": [400, 800, 50],
            "ESS_start_SoC": [0.5, 0.5, 0],
            "EV_flex": [0.5, 0.5, 0.0],
            "Export_headroom": [0, 0, 0],
            "Fixed_load1_scalar": [1, 1, 0],
            "Fixed_load2_scalar": [3, 3, 0],
            "Flex_load_max": [50, 50, 0],
            "GridExport": [95, 95, 0],
            "GridImport": [95, 95, 0],
            "Import_headroom": [0, 0, 0],
            "Min_power_factor": [0.95, 0.95, 0.0],
            "Mop_load_max": [300, 300, 0],
            "OPEX_limit": 20.0,
            "ScalarHL1": [1, 1, 0],
            "ScalarHYield": [0.75, 0.75, 0.0],
            "ScalarRG1": [600, 600, 0],
            "ScalarRG2": [100, 100, 0],
            "ScalarRG3": [50, 50, 0],
            "ScalarRG4": [0, 0, 0],
            "Export_kWh_price": 5.0,
            "f22_EV_CP_number": [3, 3, 0],
            "r50_EV_CP_number": [0, 0, 0],
            "s7_EV_CP_number": [0, 0, 0],
            "target_max_concurrency": 44,
            "time_budget_min": 1.0,
            "timestep_hours": 1.0,
            "u150_EV_CP_number": [0, 0, 0],
        }
        assert problem.input_dir == Path(
            "tests", "data", "benchmarks", "var-3", "InputData"
        )
