"""Integration tests for adding and querying optimisation tasks."""

import copy
import datetime
import json
import uuid

import httpx
import numpy as np
import pydantic
import pytest
import pytest_asyncio

from app.internal.utils.uuid import uuid7
from app.models.epoch_types import TaskDataPydantic
from app.models.epoch_types.task_data_type import Building, Grid
from app.models.optimisation import (
    OptimisationResultEntry,
    Optimiser,
    OptimiserEnum,
    PortfolioOptimisationResult,
    SimulationMetrics,
    SiteOptimisationResult,
    TaskConfig,
    TaskResult,
)


class TestOptimisationTaskDatabase:
    """Integration tests for adding and querying optimisation tasks."""

    @pytest_asyncio.fixture
    async def sample_task_config(self, client: httpx.AsyncClient) -> TaskConfig:
        """Create a sample task to put in our database."""
        bundle_id = str(uuid7())
        start_ts = datetime.datetime(year=2020, month=1, day=1, tzinfo=datetime.UTC)
        end_ts = datetime.datetime(year=2020, month=2, day=1, tzinfo=datetime.UTC)
        bundle_resp = await client.post(
            "/create-bundle",
            json={
                "bundle_id": bundle_id,
                "name": "Task Config Tests",
                "site_id": "demo_london",
                "start_ts": start_ts.isoformat(),
                "end_ts": end_ts.isoformat(),
            },
        )
        assert bundle_resp.is_success
        return TaskConfig(
            task_id=uuid7(),
            task_name="test_task_config",
            client_id="demo",
            portfolio_constraints={"capex": {"max": 1e5}},
            site_constraints={"demo_london": {"capex": {"min": 1000, "max": 9999}}},
            portfolio_range={
                "demo_london": {
                    "grid": {
                        "COMPONENT_IS_MANDATORY": True,
                        "export_headroom": [0],
                        "grid_export": [0],
                        "grid_import": [0],
                        "import_headroom": [0],
                        "min_power_factor": [0],
                        "tariff_index": [0],
                    }
                }
            },
            objectives=["capex", "carbon_balance"],
            optimiser=Optimiser(name=OptimiserEnum.NSGA2, hyperparameters={}),
            created_at=datetime.datetime.now(datetime.UTC),
            epoch_version="1.2.3",
            bundle_ids={"demo_london": bundle_id},
        )

    @pytest.fixture
    def sample_task_result(self, sample_task_config: TaskConfig) -> TaskResult:
        """Create a sample task to put in our database."""
        return TaskResult(
            task_id=sample_task_config.task_id,
            n_evals=123,
            exec_time=datetime.timedelta(hours=1, minutes=2, seconds=3),
            # completed_at=None, # deliberately left out
        )

    @pytest.fixture
    def sample_portfolio_optimisation_result(self, sample_task_config: TaskConfig) -> PortfolioOptimisationResult:
        """Create a sample result for the whole small portfolio."""
        return PortfolioOptimisationResult(
            portfolio_id=uuid7(),
            task_id=sample_task_config.task_id,
            metrics=SimulationMetrics(
                carbon_balance_scope_1=1.0,
                carbon_balance_scope_2=2.0,
                cost_balance=3.0,
                capex=4.0,
                payback_horizon=None,  # we didn't calculate this one
                annualised_cost=-1.0,  # this one is negative!
                carbon_cost=5.0,
                total_gas_used=3.0,
                total_electricity_imported=3.0,
                total_electricity_generated=3.0,
                total_electricity_exported=3.0,
            ),
        )

    @pytest.fixture
    def sample_scenario(self) -> TaskDataPydantic:
        """Create a sample scenario to put in our database."""
        task_data = TaskDataPydantic()
        task_data.building = Building(scalar_heat_load=1.0, scalar_electrical_load=1.0, fabric_intervention_index=0)
        task_data.grid = Grid(grid_export=23.0, grid_import=23.0, import_headroom=0.4, tariff_index=0)
        return task_data

    @pytest.fixture
    def sample_site_optimisation_result(
        self, sample_portfolio_optimisation_result: PortfolioOptimisationResult, sample_scenario: TaskDataPydantic
    ) -> SiteOptimisationResult:
        """Create a sample result for the one site in our portfolio."""
        return SiteOptimisationResult(
            portfolio_id=sample_portfolio_optimisation_result.portfolio_id,
            site_id="demo_london",
            scenario=sample_scenario,
            metrics=SimulationMetrics(
                carbon_balance_scope_1=1.0,
                carbon_balance_scope_2=2.0,
                cost_balance=3.0,
                capex=4.0,
                payback_horizon=None,  # we didn't calculate this one
                annualised_cost=-1.0,  # this one is negative!
                carbon_cost=5.0,
                total_gas_used=3.0,
                total_electricity_imported=3.0,
                total_electricity_generated=3.0,
                total_electricity_exported=3.0,
            ),
        )

    @pytest.mark.asyncio
    async def test_can_add_task_config(self, sample_task_config: TaskConfig, client: httpx.AsyncClient) -> None:
        """Test that we can add a simple task config."""
        result = await client.post("/add-optimisation-task", content=sample_task_config.model_dump_json())
        assert result.status_code == 200, result.text

    @pytest.mark.asyncio
    async def test_can_add_multiple_task_config(self, sample_task_config: TaskConfig, client: httpx.AsyncClient) -> None:
        """Test that we can add two task configs successfully."""
        result = await client.post("/add-optimisation-task", content=sample_task_config.model_dump_json())
        assert result.status_code == 200, result.text
        sample_task_config.task_id = uuid7()  # generate a new UUID
        result_2 = await client.post("/add-optimisation-task", content=sample_task_config.model_dump_json())
        assert result_2.status_code == 200, result.text

    @pytest.mark.asyncio
    async def test_can_add_and_retrieve_task_config(self, sample_task_config: TaskConfig, client: httpx.AsyncClient) -> None:
        """Test that we can add a task config and retrieve it with no results associated."""
        result = await client.post("/add-optimisation-task", content=sample_task_config.model_dump_json())
        assert result.status_code == 200, result.text
        result_2 = await client.post("/list-optimisation-tasks", content=json.dumps({"client_id": "demo"}))
        assert result_2.status_code == 200, result_2.text

        listed_tasks = result_2.json()
        assert len(listed_tasks) == 1
        assert listed_tasks[0]["task_name"] == "test_task_config"
        assert listed_tasks[0]["task_id"] == str(sample_task_config.task_id)
        assert listed_tasks[0]["n_saved"] == 0, "We should have no portfolio results saved for this task"

    @pytest.mark.asyncio
    async def test_can_add_portfolio_results_no_site(
        self,
        sample_task_config: TaskConfig,
        sample_portfolio_optimisation_result: PortfolioOptimisationResult,
        client: httpx.AsyncClient,
    ) -> None:
        """Test that we can add a portfolio result with no site data."""
        result = await client.post("/add-optimisation-task", content=sample_task_config.model_dump_json())
        assert result.status_code == 200, result.text

        opt_result = await client.post(
            "/add-optimisation-results",
            content=OptimisationResultEntry(portfolio=[sample_portfolio_optimisation_result]).model_dump_json(),
        )
        assert opt_result.status_code == 200, opt_result.text

    @pytest.mark.asyncio
    async def test_can_get_portfolio_results_no_site(
        self,
        sample_task_config: TaskConfig,
        sample_portfolio_optimisation_result: PortfolioOptimisationResult,
        client: httpx.AsyncClient,
    ) -> None:
        """Test that we can add a portfolio result with no site data around."""
        result = await client.post("/add-optimisation-task", content=sample_task_config.model_dump_json())
        assert result.status_code == 200, result.text

        opt_result = await client.post(
            "/add-optimisation-results",
            content=OptimisationResultEntry(portfolio=[sample_portfolio_optimisation_result]).model_dump_json(),
        )
        assert opt_result.status_code == 200, opt_result.text

        get_result = await client.post(
            "/get-optimisation-results", content=json.dumps({"task_id": str(sample_task_config.task_id)})
        )
        assert get_result.status_code == 200, get_result.text
        portfolio_results = get_result.json()["portfolio_results"]
        assert len(portfolio_results) == 1
        assert portfolio_results[0]["task_id"] == str(sample_task_config.task_id)
        assert portfolio_results[0]["portfolio_id"] == str(sample_portfolio_optimisation_result.portfolio_id)
        assert portfolio_results[0]["site_results"] is None

        # check that we don't highlight results for the same reason more than once
        highlighted_results = get_result.json()["highlighted_results"]
        assert len(highlighted_results) == len({highlight["reason"] for highlight in highlighted_results})

    @pytest.mark.asyncio
    async def test_can_add_portfolio_results_one_site(
        self,
        sample_task_config: TaskConfig,
        sample_portfolio_optimisation_result: PortfolioOptimisationResult,
        sample_site_optimisation_result: SiteOptimisationResult,
        client: httpx.AsyncClient,
    ) -> None:
        """Test that we can add a portfolio result with the associated site data bundled."""
        result = await client.post("/add-optimisation-task", content=sample_task_config.model_dump_json())
        assert result.status_code == 200, result.text
        sample_portfolio_optimisation_result.site_results = [sample_site_optimisation_result]
        to_send = OptimisationResultEntry(portfolio=[sample_portfolio_optimisation_result])
        opt_result = await client.post("/add-optimisation-results", content=to_send.model_dump_json())
        assert opt_result.status_code == 200, opt_result.text

    @pytest.mark.asyncio
    async def test_site_flt_max(
        self,
        sample_task_config: TaskConfig,
        sample_portfolio_optimisation_result: PortfolioOptimisationResult,
        sample_site_optimisation_result: SiteOptimisationResult,
        client: httpx.AsyncClient,
    ) -> None:
        """Test that we can add a site with a FLT_MAX result."""
        result = await client.post("/add-optimisation-task", content=sample_task_config.model_dump_json())
        assert result.status_code == 200, result.text

        sample_site_optimisation_result.metrics.cost_balance = float(np.finfo(np.float32).max) + 1.0
        sample_site_result_2 = copy.deepcopy(sample_site_optimisation_result)
        sample_site_result_2.site_id = "demo_edinburgh"

        sample_portfolio_optimisation_result.site_results = [sample_site_optimisation_result, sample_site_result_2]
        sample_portfolio_optimisation_result.metrics.cost_balance = float(np.finfo(np.float32).max)
        to_send = OptimisationResultEntry(portfolio=[sample_portfolio_optimisation_result])
        opt_result = await client.post("/add-optimisation-results", content=to_send.model_dump_json())
        assert opt_result.status_code == 200, opt_result.text
        get_result = await client.post(
            "/get-optimisation-results", content=json.dumps({"task_id": str(sample_task_config.task_id)})
        )
        assert get_result.status_code == 200, get_result.text
        portfolio_results = get_result.json()["portfolio_results"]
        assert portfolio_results[0]["metrics"]["cost_balance"] == float(np.finfo(np.float32).max)
        assert portfolio_results[0]["site_results"][0]["metrics"]["cost_balance"] == float(np.finfo(np.float32).max)

    @pytest.mark.asyncio
    async def test_site_inf(
        self,
        sample_task_config: TaskConfig,
        sample_portfolio_optimisation_result: PortfolioOptimisationResult,
        sample_site_optimisation_result: SiteOptimisationResult,
        client: httpx.AsyncClient,
    ) -> None:
        """Test that we can add a site with an inf result and not immediately fall over."""
        result = await client.post("/add-optimisation-task", content=sample_task_config.model_dump_json())
        assert result.status_code == 200, result.text

        sample_site_optimisation_result.metrics.cost_balance = float("inf")
        sample_site_result_2 = copy.deepcopy(sample_site_optimisation_result)
        sample_site_result_2.site_id = "demo_edinburgh"

        sample_portfolio_optimisation_result.site_results = [sample_site_optimisation_result, sample_site_result_2]
        sample_portfolio_optimisation_result.metrics.cost_balance = float("inf")
        to_send = OptimisationResultEntry(portfolio=[sample_portfolio_optimisation_result])
        opt_result = await client.post("/add-optimisation-results", content=to_send.model_dump_json())
        assert opt_result.status_code == 200, opt_result.text
        get_result = await client.post(
            "/get-optimisation-results", content=json.dumps({"task_id": str(sample_task_config.task_id)})
        )
        assert get_result.status_code == 200, get_result.text
        portfolio_results = get_result.json()["portfolio_results"]
        assert portfolio_results[0]["metrics"]["cost_balance"] is None
        assert portfolio_results[0]["site_results"][0]["metrics"]["cost_balance"] is None

    @pytest.mark.asyncio
    async def test_can_get_portfolio_results_one_site(
        self,
        sample_task_config: TaskConfig,
        sample_portfolio_optimisation_result: PortfolioOptimisationResult,
        sample_site_optimisation_result: SiteOptimisationResult,
        client: httpx.AsyncClient,
    ) -> None:
        """Test that we can get a portfolio result with the associated site data bundled."""
        result = await client.post("/add-optimisation-task", content=sample_task_config.model_dump_json())
        assert result.status_code == 200, result.text
        sample_portfolio_optimisation_result.site_results = [sample_site_optimisation_result]
        opt_result = await client.post(
            "/add-optimisation-results",
            content=OptimisationResultEntry(portfolio=[sample_portfolio_optimisation_result]).model_dump_json(),
        )
        assert opt_result.status_code == 200, opt_result.text

        get_result = await client.post(
            "/get-optimisation-results", content=json.dumps({"task_id": str(sample_task_config.task_id)})
        )
        assert get_result.status_code == 200, get_result.text
        portfolio_results = get_result.json()["portfolio_results"]
        assert portfolio_results[0]["task_id"] == str(sample_task_config.task_id)
        assert portfolio_results[0]["portfolio_id"] == str(sample_portfolio_optimisation_result.portfolio_id)
        assert len(portfolio_results[0]["site_results"]) == 1
        assert portfolio_results[0]["site_results"][0]["scenario"] == sample_site_optimisation_result.model_dump()["scenario"]
        assert (
            portfolio_results[0]["site_results"][0]["metrics"]["capex"]
            == sample_site_optimisation_result.model_dump()["metrics"]["capex"]
        )
        assert (
            portfolio_results[0]["site_results"][0]["metrics"]["total_gas_used"]
            == sample_site_optimisation_result.model_dump()["metrics"]["total_gas_used"]
        )

    @pytest.mark.asyncio
    async def test_can_handle_result_with_no_metrics(self, sample_task_config: TaskConfig, client: httpx.AsyncClient) -> None:
        """Test that we can add a result with no metrics and get it back."""
        result = await client.post("/add-optimisation-task", content=sample_task_config.model_dump_json())
        assert result.status_code == 200, result.text

        empty_portfolio_result = PortfolioOptimisationResult(
            portfolio_id=uuid7(),
            task_id=sample_task_config.task_id,
            metrics=SimulationMetrics(),  # no metrics recorded
            site_results=[],
        )

        opt_result = await client.post(
            "/add-optimisation-results",
            content=OptimisationResultEntry(portfolio=[empty_portfolio_result]).model_dump_json(),
        )
        assert opt_result.status_code == 200, opt_result.text

        get_result = await client.post(
            "/get-optimisation-results", content=json.dumps({"task_id": str(sample_task_config.task_id)})
        )
        assert get_result.status_code == 200, get_result.text
        portfolio_results = get_result.json()["portfolio_results"]
        assert portfolio_results[0]["task_id"] == str(sample_task_config.task_id)
        assert portfolio_results[0]["portfolio_id"] == str(empty_portfolio_result.portfolio_id)

        # All metrics should be None, check a few of them
        assert portfolio_results[0]["metrics"]["carbon_cost"] is None
        assert portfolio_results[0]["metrics"]["total_heat_shortfall"] is None
        assert portfolio_results[0]["metrics"]["total_dhw_shortfall"] is None
        assert portfolio_results[0]["metrics"]["total_electricity_export_gain"] is None

    @pytest.mark.asyncio
    async def test_can_get_repro_results(
        self,
        sample_task_config: TaskConfig,
        sample_portfolio_optimisation_result: PortfolioOptimisationResult,
        sample_site_optimisation_result: SiteOptimisationResult,
        client: httpx.AsyncClient,
    ) -> None:
        """Test that we can get a reproduction result for a single site in a portfolio."""
        result = await client.post("/add-optimisation-task", content=sample_task_config.model_dump_json())
        assert result.status_code == 200, result.text
        sample_portfolio_optimisation_result.site_results = [sample_site_optimisation_result]
        opt_result = await client.post(
            "/add-optimisation-results",
            content=OptimisationResultEntry(portfolio=[sample_portfolio_optimisation_result]).model_dump_json(),
        )
        assert opt_result.status_code == 200, opt_result.text

        get_result = await client.post(
            "/get-optimisation-results", content=json.dumps({"task_id": str(sample_task_config.task_id)})
        )
        assert get_result.status_code == 200, get_result.text

        repro_result = await client.post(
            "/get-result-configuration",
            content=json.dumps({"result_id": str(sample_portfolio_optimisation_result.portfolio_id)}),
        )
        assert repro_result.status_code == 200, repro_result.text
        repro_data = repro_result.json()
        assert repro_data["portfolio_id"] == str(sample_portfolio_optimisation_result.portfolio_id)

        assert repro_data["bundle_ids"]["demo_london"] == str(sample_task_config.bundle_ids["demo_london"])
        assert repro_data["task_data"] == {
            sample_site_optimisation_result.site_id: sample_site_optimisation_result.scenario.model_dump()
        }

    @pytest.mark.asyncio
    async def test_can_retrieve_task_result(
        self, sample_task_config: TaskConfig, sample_task_result: TaskResult, client: httpx.AsyncClient
    ) -> None:
        """Test that we can add a task config and retrieve it with no results associated."""
        result = await client.post("/add-optimisation-task", content=sample_task_config.model_dump_json())
        assert result.status_code == 200, result.text

        res_result = await client.post(
            "/add-optimisation-results", content=OptimisationResultEntry(tasks=[sample_task_result]).model_dump_json()
        )
        assert res_result.status_code == 200, res_result.text

        list_result = await client.post("/list-optimisation-tasks", content=json.dumps({"client_id": "demo"}))
        assert list_result.status_code == 200, list_result.text
        assert list_result.json()[0]["task_id"] == str(sample_task_config.task_id)
        assert list_result.json()[0]["n_evals"] == 123
        assert list_result.json()[0]["exec_time"] == pydantic.TypeAdapter(datetime.timedelta).dump_python(
            sample_task_result.exec_time, mode="json"
        )

    @pytest.mark.asyncio
    async def test_can_add_multiple_portfolio_results(
        self,
        sample_task_config: TaskConfig,
        sample_portfolio_optimisation_result: PortfolioOptimisationResult,
        client: httpx.AsyncClient,
    ) -> None:
        """Test that adding a task with two portfolio results returns a result with two results saved."""
        task_response = await client.post("/add-optimisation-task", content=sample_task_config.model_dump_json())
        assert task_response.status_code == 200, task_response.text

        portfolio_result_1 = sample_portfolio_optimisation_result.model_copy(update={"portfolio_id": uuid7()})
        portfolio_result_2 = sample_portfolio_optimisation_result.model_copy(update={"portfolio_id": uuid7()})

        opt_result = OptimisationResultEntry(portfolio=[portfolio_result_1, portfolio_result_2])
        result_response = await client.post("/add-optimisation-results", content=opt_result.model_dump_json())
        assert result_response.status_code == 200, result_response.text

        list_tasks_response = await client.post("/list-optimisation-tasks", content=json.dumps({"client_id": "demo"}))
        assert list_tasks_response.status_code == 200, list_tasks_response.text

        tasks = list_tasks_response.json()
        # There should be exactly one task with n_saved = 2
        assert len(tasks) == 1, "There should be exactly one listed task."
        assert tasks[0]["n_saved"] == 2, f"Expected n_saved to be 2 - got {tasks[0]['n_saved']} instead."


class TestOptimisationTaskDatabaseUUID4:
    """Integration tests for adding and querying optimisation tasks with old-style UUID4s."""

    @pytest_asyncio.fixture
    async def sample_task_config(self, client: httpx.AsyncClient) -> TaskConfig:
        """Create a sample task to put in our database."""
        bundle_id = str(uuid.uuid4())
        start_ts = datetime.datetime(year=2020, month=1, day=1, tzinfo=datetime.UTC)
        end_ts = datetime.datetime(year=2020, month=2, day=1, tzinfo=datetime.UTC)
        bundle_resp = await client.post(
            "/create-bundle",
            json={
                "bundle_id": bundle_id,
                "name": "Task Config Tests",
                "site_id": "demo_london",
                "start_ts": start_ts.isoformat(),
                "end_ts": end_ts.isoformat(),
            },
        )
        assert bundle_resp.is_success
        return TaskConfig(
            task_id=uuid.uuid4(),
            task_name="test_task_config",
            client_id="demo",
            portfolio_constraints={"capex": {"max": 1e5}},
            site_constraints={"demo_london": {"capex": {"min": 1000, "max": 9999}}},
            portfolio_range={
                "demo_london": {
                    "grid": {
                        "COMPONENT_IS_MANDATORY": True,
                        "export_headroom": [0],
                        "grid_export": [0],
                        "grid_import": [0],
                        "import_headroom": [0],
                        "min_power_factor": [0],
                        "tariff_index": [0],
                    }
                }
            },
            objectives=["capex", "carbon_balance"],
            optimiser=Optimiser(name=OptimiserEnum.NSGA2, hyperparameters={}),
            created_at=datetime.datetime.now(datetime.UTC),
            epoch_version="v1.2.3",
            bundle_ids={"demo_london": bundle_id},
        )

    @pytest.fixture
    def sample_task_result(self, sample_task_config: TaskConfig) -> TaskResult:
        """Create a sample task to put in our database."""
        return TaskResult(
            task_id=sample_task_config.task_id,
            n_evals=123,
            exec_time=datetime.timedelta(hours=1, minutes=2, seconds=3),
            # completed_at=None, # deliberately left out
        )

    @pytest.fixture
    def sample_portfolio_optimisation_result(self, sample_task_config: TaskConfig) -> PortfolioOptimisationResult:
        """Create a sample result for the whole small portfolio."""
        return PortfolioOptimisationResult(
            portfolio_id=uuid.uuid4(),
            task_id=sample_task_config.task_id,
            metrics=SimulationMetrics(
                carbon_balance_scope_1=1.0,
                carbon_balance_scope_2=2.0,
                cost_balance=3.0,
                capex=4.0,
                payback_horizon=None,  # we didn't calculate this one
                annualised_cost=-1.0,  # this one is negative!
                carbon_cost=5.0,
                total_gas_used=3.0,
                total_electricity_imported=3.0,
                total_electricity_generated=3.0,
                total_electricity_exported=3.0,
            ),
        )

    @pytest.fixture
    def sample_scenario(self) -> TaskDataPydantic:
        """Create a sample scenario to put in our database."""
        task_data = TaskDataPydantic()
        task_data.building = Building(scalar_heat_load=1.0, scalar_electrical_load=1.0, fabric_intervention_index=0)
        task_data.grid = Grid(grid_export=23.0, grid_import=23.0, import_headroom=0.4, tariff_index=0)
        return task_data

    @pytest.fixture
    def sample_site_optimisation_result(
        self, sample_portfolio_optimisation_result: PortfolioOptimisationResult, sample_scenario: TaskDataPydantic
    ) -> SiteOptimisationResult:
        """Create a sample result for the one site in our portfolio."""
        return SiteOptimisationResult(
            portfolio_id=sample_portfolio_optimisation_result.portfolio_id,
            site_id="demo_london",
            scenario=sample_scenario,
            metrics=SimulationMetrics(
                carbon_balance_scope_1=1.0,
                carbon_balance_scope_2=2.0,
                cost_balance=3.0,
                capex=4.0,
                payback_horizon=None,  # we didn't calculate this one
                annualised_cost=-1.0,  # this one is negative!
                carbon_cost=5.0,
                total_gas_used=3.0,
                total_electricity_imported=3.0,
                total_electricity_generated=3.0,
                total_electricity_exported=3.0,
            ),
        )

    @pytest.mark.asyncio
    async def test_can_add_task_config(self, sample_task_config: TaskConfig, client: httpx.AsyncClient) -> None:
        """Test that we can add a simple task config."""
        result = await client.post("/add-optimisation-task", content=sample_task_config.model_dump_json())
        assert result.status_code == 200, result.text

    @pytest.mark.asyncio
    async def test_can_add_multiple_task_config(self, sample_task_config: TaskConfig, client: httpx.AsyncClient) -> None:
        """Test that we can add two task configs successfully."""
        result = await client.post("/add-optimisation-task", content=sample_task_config.model_dump_json())
        assert result.status_code == 200, result.text
        sample_task_config.task_id = uuid.uuid4()  # generate a new UUID
        result_2 = await client.post("/add-optimisation-task", content=sample_task_config.model_dump_json())
        assert result_2.status_code == 200, result.text

    @pytest.mark.asyncio
    async def test_can_add_and_retrieve_task_config(self, sample_task_config: TaskConfig, client: httpx.AsyncClient) -> None:
        """Test that we can add a task config and retrieve it with no results associated."""
        result = await client.post("/add-optimisation-task", content=sample_task_config.model_dump_json())
        assert result.status_code == 200, result.text
        result_2 = await client.post("/list-optimisation-tasks", content=json.dumps({"client_id": "demo"}))
        assert result_2.status_code == 200, result_2.text

        listed_tasks = result_2.json()
        assert len(listed_tasks) == 1
        assert listed_tasks[0]["task_name"] == "test_task_config"
        assert listed_tasks[0]["task_id"] == str(sample_task_config.task_id)
        assert listed_tasks[0]["n_saved"] == 0, "We should have no portfolio results saved for this task"

    @pytest.mark.asyncio
    async def test_can_add_portfolio_results_no_site(
        self,
        sample_task_config: TaskConfig,
        sample_portfolio_optimisation_result: PortfolioOptimisationResult,
        client: httpx.AsyncClient,
    ) -> None:
        """Test that we can add a portfolio result with no site data."""
        result = await client.post("/add-optimisation-task", content=sample_task_config.model_dump_json())
        assert result.status_code == 200, result.text

        opt_result = await client.post(
            "/add-optimisation-results",
            content=OptimisationResultEntry(portfolio=[sample_portfolio_optimisation_result]).model_dump_json(),
        )
        assert opt_result.status_code == 200, opt_result.text

    @pytest.mark.asyncio
    async def test_can_get_portfolio_results_no_site(
        self,
        sample_task_config: TaskConfig,
        sample_portfolio_optimisation_result: PortfolioOptimisationResult,
        client: httpx.AsyncClient,
    ) -> None:
        """Test that we can add a portfolio result with no site data around."""
        result = await client.post("/add-optimisation-task", content=sample_task_config.model_dump_json())
        assert result.status_code == 200, result.text

        opt_result = await client.post(
            "/add-optimisation-results",
            content=OptimisationResultEntry(portfolio=[sample_portfolio_optimisation_result]).model_dump_json(),
        )
        assert opt_result.status_code == 200, opt_result.text

        get_result = await client.post(
            "/get-optimisation-results", content=json.dumps({"task_id": str(sample_task_config.task_id)})
        )
        assert get_result.status_code == 200, get_result.text
        portfolio_results = get_result.json()["portfolio_results"]
        assert len(portfolio_results) == 1
        assert portfolio_results[0]["task_id"] == str(sample_task_config.task_id)
        assert portfolio_results[0]["portfolio_id"] == str(sample_portfolio_optimisation_result.portfolio_id)
        assert portfolio_results[0]["site_results"] is None

        # check that we don't highlight results for the same reason more than once
        highlighted_results = get_result.json()["highlighted_results"]
        assert len(highlighted_results) == len({highlight["reason"] for highlight in highlighted_results})

    @pytest.mark.asyncio
    async def test_can_add_portfolio_results_one_site(
        self,
        sample_task_config: TaskConfig,
        sample_portfolio_optimisation_result: PortfolioOptimisationResult,
        sample_site_optimisation_result: SiteOptimisationResult,
        client: httpx.AsyncClient,
    ) -> None:
        """Test that we can add a portfolio result with the associated site data bundled."""
        result = await client.post("/add-optimisation-task", content=sample_task_config.model_dump_json())
        assert result.status_code == 200, result.text
        sample_portfolio_optimisation_result.site_results = [sample_site_optimisation_result]
        to_send = OptimisationResultEntry(portfolio=[sample_portfolio_optimisation_result])
        opt_result = await client.post("/add-optimisation-results", content=to_send.model_dump_json())
        assert opt_result.status_code == 200, opt_result.text

    @pytest.mark.asyncio
    async def test_site_flt_max(
        self,
        sample_task_config: TaskConfig,
        sample_portfolio_optimisation_result: PortfolioOptimisationResult,
        sample_site_optimisation_result: SiteOptimisationResult,
        client: httpx.AsyncClient,
    ) -> None:
        """Test that we can add a site with a FLT_MAX result."""
        result = await client.post("/add-optimisation-task", content=sample_task_config.model_dump_json())
        assert result.status_code == 200, result.text

        sample_site_optimisation_result.metrics.cost_balance = float(np.finfo(np.float32).max) + 1.0
        sample_site_result_2 = copy.deepcopy(sample_site_optimisation_result)
        sample_site_result_2.site_id = "demo_edinburgh"

        sample_portfolio_optimisation_result.site_results = [sample_site_optimisation_result, sample_site_result_2]
        sample_portfolio_optimisation_result.metrics.cost_balance = float(np.finfo(np.float32).max)
        to_send = OptimisationResultEntry(portfolio=[sample_portfolio_optimisation_result])
        opt_result = await client.post("/add-optimisation-results", content=to_send.model_dump_json())
        assert opt_result.status_code == 200, opt_result.text
        get_result = await client.post(
            "/get-optimisation-results", content=json.dumps({"task_id": str(sample_task_config.task_id)})
        )
        assert get_result.status_code == 200, get_result.text
        portfolio_results = get_result.json()["portfolio_results"]
        assert portfolio_results[0]["metrics"]["cost_balance"] == float(np.finfo(np.float32).max)
        assert portfolio_results[0]["site_results"][0]["metrics"]["cost_balance"] == float(np.finfo(np.float32).max)

    @pytest.mark.asyncio
    async def test_site_inf(
        self,
        sample_task_config: TaskConfig,
        sample_portfolio_optimisation_result: PortfolioOptimisationResult,
        sample_site_optimisation_result: SiteOptimisationResult,
        client: httpx.AsyncClient,
    ) -> None:
        """Test that we can add a site with an inf result and not immediately fall over."""
        result = await client.post("/add-optimisation-task", content=sample_task_config.model_dump_json())
        assert result.status_code == 200, result.text

        sample_site_optimisation_result.metrics.cost_balance = float("inf")
        sample_site_result_2 = copy.deepcopy(sample_site_optimisation_result)
        sample_site_result_2.site_id = "demo_edinburgh"

        sample_portfolio_optimisation_result.site_results = [sample_site_optimisation_result, sample_site_result_2]
        sample_portfolio_optimisation_result.metrics.cost_balance = float("inf")
        to_send = OptimisationResultEntry(portfolio=[sample_portfolio_optimisation_result])
        opt_result = await client.post("/add-optimisation-results", content=to_send.model_dump_json())
        assert opt_result.status_code == 200, opt_result.text
        get_result = await client.post(
            "/get-optimisation-results", content=json.dumps({"task_id": str(sample_task_config.task_id)})
        )
        assert get_result.status_code == 200, get_result.text
        portfolio_results = get_result.json()["portfolio_results"]
        assert portfolio_results[0]["metrics"]["cost_balance"] is None
        assert portfolio_results[0]["site_results"][0]["metrics"]["cost_balance"] is None

    @pytest.mark.asyncio
    async def test_can_get_portfolio_results_one_site(
        self,
        sample_task_config: TaskConfig,
        sample_portfolio_optimisation_result: PortfolioOptimisationResult,
        sample_site_optimisation_result: SiteOptimisationResult,
        client: httpx.AsyncClient,
    ) -> None:
        """Test that we can get a portfolio result with the associated site data bundled."""
        result = await client.post("/add-optimisation-task", content=sample_task_config.model_dump_json())
        assert result.status_code == 200, result.text
        sample_portfolio_optimisation_result.site_results = [sample_site_optimisation_result]
        opt_result = await client.post(
            "/add-optimisation-results",
            content=OptimisationResultEntry(portfolio=[sample_portfolio_optimisation_result]).model_dump_json(),
        )
        assert opt_result.status_code == 200, opt_result.text

        get_result = await client.post(
            "/get-optimisation-results", content=json.dumps({"task_id": str(sample_task_config.task_id)})
        )
        assert get_result.status_code == 200, get_result.text
        portfolio_results = get_result.json()["portfolio_results"]
        assert portfolio_results[0]["task_id"] == str(sample_task_config.task_id)
        assert portfolio_results[0]["portfolio_id"] == str(sample_portfolio_optimisation_result.portfolio_id)
        assert len(portfolio_results[0]["site_results"]) == 1
        assert portfolio_results[0]["site_results"][0]["scenario"] == sample_site_optimisation_result.model_dump()["scenario"]
        assert (
            portfolio_results[0]["site_results"][0]["metrics"]["capex"]
            == sample_site_optimisation_result.model_dump()["metrics"]["capex"]
        )
        assert (
            portfolio_results[0]["site_results"][0]["metrics"]["total_gas_used"]
            == sample_site_optimisation_result.model_dump()["metrics"]["total_gas_used"]
        )

    @pytest.mark.asyncio
    async def test_can_handle_result_with_no_metrics(self, sample_task_config: TaskConfig, client: httpx.AsyncClient) -> None:
        """Test that we can add a result with no metrics and get it back."""
        result = await client.post("/add-optimisation-task", content=sample_task_config.model_dump_json())
        assert result.status_code == 200, result.text

        empty_portfolio_result = PortfolioOptimisationResult(
            portfolio_id=uuid7(),
            task_id=sample_task_config.task_id,
            metrics=SimulationMetrics(),  # no metrics recorded
            site_results=[],
        )

        opt_result = await client.post(
            "/add-optimisation-results",
            content=OptimisationResultEntry(portfolio=[empty_portfolio_result]).model_dump_json(),
        )
        assert opt_result.status_code == 200, opt_result.text

        get_result = await client.post(
            "/get-optimisation-results", content=json.dumps({"task_id": str(sample_task_config.task_id)})
        )
        assert get_result.status_code == 200, get_result.text
        portfolio_results = get_result.json()["portfolio_results"]
        assert portfolio_results[0]["task_id"] == str(sample_task_config.task_id)
        assert portfolio_results[0]["portfolio_id"] == str(empty_portfolio_result.portfolio_id)

        # All metrics should be None, check a few of them
        assert portfolio_results[0]["metrics"]["carbon_cost"] is None
        assert portfolio_results[0]["metrics"]["total_heat_shortfall"] is None
        assert portfolio_results[0]["metrics"]["total_dhw_shortfall"] is None
        assert portfolio_results[0]["metrics"]["total_electricity_export_gain"] is None

    @pytest.mark.asyncio
    async def test_can_get_repro_results(
        self,
        sample_task_config: TaskConfig,
        sample_portfolio_optimisation_result: PortfolioOptimisationResult,
        sample_site_optimisation_result: SiteOptimisationResult,
        client: httpx.AsyncClient,
    ) -> None:
        """Test that we can get a reproduction result for a single site in a portfolio."""
        result = await client.post("/add-optimisation-task", content=sample_task_config.model_dump_json())
        assert result.status_code == 200, result.text
        sample_portfolio_optimisation_result.site_results = [sample_site_optimisation_result]
        opt_result = await client.post(
            "/add-optimisation-results",
            content=OptimisationResultEntry(portfolio=[sample_portfolio_optimisation_result]).model_dump_json(),
        )
        assert opt_result.status_code == 200, opt_result.text

        get_result = await client.post(
            "/get-optimisation-results", content=json.dumps({"task_id": str(sample_task_config.task_id)})
        )
        assert get_result.status_code == 200, get_result.text

        repro_result = await client.post(
            "/get-result-configuration",
            content=json.dumps({"result_id": str(sample_portfolio_optimisation_result.portfolio_id)}),
        )
        assert repro_result.status_code == 200, repro_result.text
        repro_data = repro_result.json()
        assert repro_data["portfolio_id"] == str(sample_portfolio_optimisation_result.portfolio_id)

        assert repro_data["bundle_ids"]["demo_london"] == str(sample_task_config.bundle_ids["demo_london"])
        assert repro_data["task_data"] == {
            sample_site_optimisation_result.site_id: sample_site_optimisation_result.scenario.model_dump()
        }

    @pytest.mark.asyncio
    async def test_can_retrieve_task_result(
        self, sample_task_config: TaskConfig, sample_task_result: TaskResult, client: httpx.AsyncClient
    ) -> None:
        """Test that we can add a task config and retrieve it with no results associated."""
        result = await client.post("/add-optimisation-task", content=sample_task_config.model_dump_json())
        assert result.status_code == 200, result.text

        res_result = await client.post(
            "/add-optimisation-results", content=OptimisationResultEntry(tasks=[sample_task_result]).model_dump_json()
        )
        assert res_result.status_code == 200, res_result.text

        list_result = await client.post("/list-optimisation-tasks", content=json.dumps({"client_id": "demo"}))
        assert list_result.status_code == 200, list_result.text
        assert list_result.json()[0]["task_id"] == str(sample_task_config.task_id)
        assert list_result.json()[0]["n_evals"] == 123
        assert list_result.json()[0]["exec_time"] == pydantic.TypeAdapter(datetime.timedelta).dump_python(
            sample_task_result.exec_time, mode="json"
        )

    @pytest.mark.asyncio
    async def test_can_add_multiple_portfolio_results(
        self,
        sample_task_config: TaskConfig,
        sample_portfolio_optimisation_result: PortfolioOptimisationResult,
        client: httpx.AsyncClient,
    ) -> None:
        """Test that adding a task with two portfolio results returns a result with two results saved."""
        task_response = await client.post("/add-optimisation-task", content=sample_task_config.model_dump_json())
        assert task_response.status_code == 200, task_response.text

        portfolio_result_1 = sample_portfolio_optimisation_result.model_copy(update={"portfolio_id": uuid.uuid4()})
        portfolio_result_2 = sample_portfolio_optimisation_result.model_copy(update={"portfolio_id": uuid.uuid4()})

        opt_result = OptimisationResultEntry(portfolio=[portfolio_result_1, portfolio_result_2])
        result_response = await client.post("/add-optimisation-results", content=opt_result.model_dump_json())
        assert result_response.status_code == 200, result_response.text

        list_tasks_response = await client.post("/list-optimisation-tasks", content=json.dumps({"client_id": "demo"}))
        assert list_tasks_response.status_code == 200, list_tasks_response.text

        tasks = list_tasks_response.json()
        # There should be exactly one task with n_saved = 2
        assert len(tasks) == 1, "There should be exactly one listed task."
        assert tasks[0]["n_saved"] == 2, f"Expected n_saved to be 2 - got {tasks[0]['n_saved']} instead."
