from os import PathLike

import pytest

from app.internal.problem import Building, Objectives, PortfolioProblem
from app.models.constraints import ConstraintDict
from app.models.parameters import ParameterDict


class TestBuilding:
    def test_good_inputs(self, default_parameters: ParameterDict, default_input_dir: PathLike) -> None:
        """
        Test that the building class works with valid input.
        """
        Building(parameters=default_parameters, input_dir=default_input_dir)

    def test_bad_paramter(self, default_parameters: ParameterDict, default_input_dir: PathLike) -> None:
        """
        Test that the building class works with valid input.
        """
        parameters = default_parameters
        parameters["pool_size"] = {"min": "Bangweulu", "max": "Caspian Sea", "step": "cubic metre"}  # type: ignore
        with pytest.raises(ValueError):
            Building(parameters=parameters, input_dir=default_input_dir)

    def test_bad_parameter_bounds(self, default_parameters: ParameterDict, default_input_dir: PathLike) -> None:
        """
        Test that we can't set bad parameter bounds, lower bound greater than upper bound.
        """
        parameters = default_parameters
        parameters["ASHP_HPower"] = {"min": 10, "max": 0, "step": 10}
        with pytest.raises(ValueError):
            Building(parameters=parameters, input_dir=default_input_dir)

    def test_bad_parameter_stepsize(self, default_parameters: ParameterDict, default_input_dir: PathLike) -> None:
        """
        Test that we can't set bad parameter stepsize.
        """
        parameters = default_parameters
        parameters["ASHP_HPower"] = {"min": 0, "max": 10, "step": 0}
        with pytest.raises(ValueError):
            Building(parameters=parameters, input_dir=default_input_dir)

    def test_size(self, default_parameters: ParameterDict, default_input_dir: PathLike) -> None:
        """
        Test that the size method returns the correct search space size.
        """

        problem = Building(parameters=default_parameters, input_dir=default_input_dir)
        assert problem.size() == 3 * 3 * 3

    def test_variable_parameters(self, default_parameters: ParameterDict, default_input_dir: PathLike) -> None:
        """
        Test that the variable_param method returns the correct search space variables.
        """
        problem = Building(parameters=default_parameters, input_dir=default_input_dir)
        assert problem.variable_param() == {
            "ESS_capacity": {"min": 1, "max": 3, "step": 1},
            "ESS_charge_power": {"min": 1, "max": 3, "step": 1},
            "ESS_discharge_power": {"min": 1, "max": 3, "step": 1},
        }

    def test_constant_parameters(self, default_parameters: ParameterDict, default_input_dir: PathLike) -> None:
        """
        Test that the ss_constants method returns the correct search space constants.
        """
        problem = Building(parameters=default_parameters, input_dir=default_input_dir)
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
            "DHW_cylinder_volume": 100,
            "timewindow": 8760,
        }


class TestPortfolioProblem:
    def test_good_inputs(
        self, default_objectives: list[Objectives], default_constraints: ConstraintDict, default_buildings: dict[str, Building]
    ) -> None:
        """
        Test that the problem class works with valid input.
        """
        PortfolioProblem(objectives=default_objectives, constraints=default_constraints, buildings=default_buildings)

    def test_bad_objective(
        self, default_objectives: list[Objectives], default_constraints: ConstraintDict, default_buildings: dict[str, Building]
    ) -> None:
        """
        Test that we can't set bad objective names.
        """
        objectives = default_objectives
        objectives.append("amazingness")  # type: ignore
        with pytest.raises(ValueError):
            PortfolioProblem(objectives=objectives, constraints=default_constraints, buildings=default_buildings)  # type: ignore

    def test_bad_constraint_names(
        self, default_objectives: list[Objectives], default_constraints: ConstraintDict, default_buildings: dict[str, Building]
    ) -> None:
        """
        Test that we can't set constraints with bad objective names.
        """
        constraints = default_constraints
        constraints["amazingness"] = {"min": 6000}  # type: ignore
        with pytest.raises(ValueError):
            PortfolioProblem(objectives=default_objectives, constraints=constraints, buildings=default_buildings)  # type: ignore

    def test_bad_constraint_bound_values(
        self, default_objectives: list[Objectives], default_constraints: ConstraintDict, default_buildings: dict[str, Building]
    ) -> None:
        """
        Test that we can't set bad constraint bounds, lower bound greater than upper bound.
        """
        constraints = default_constraints
        constraints["capex"] = {"min": 10, "max": 0}  # type: ignore
        with pytest.raises(ValueError):
            PortfolioProblem(objectives=default_objectives, constraints=constraints, buildings=default_buildings)

    def test_split_objectives(self, default_portfolio_problem) -> None:
        """
        Test that MOO problems are correctly split into SOO problems.
        """
        problem = default_portfolio_problem
        objectives = problem.objectives
        single_problems = [
            PortfolioProblem(objectives=[objective], constraints=problem.constraints, buildings=problem.buildings)
            for objective in objectives
        ]
        assert list(problem.split_objectives()) == single_problems
