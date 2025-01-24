"""Integration tests for adding and querying optimisation tasks."""

# ruff: noqa: D101, D102, D103
import datetime
import json
import uuid

import httpx
import pytest

from app.models.optimisation import (
    DataDuration,
    OptimisationResultEntry,
    Optimiser,
    OptimiserEnum,
    PortfolioOptimisationResult,
    RemoteMetaData,
    SearchSpaceEntry,
    SiteOptimisationResult,
    TaskConfig,
    TaskResult,
)


class TestOptimisationTaskDatabase:
    """Integration tests for adding and querying optimisation tasks."""

    @pytest.fixture
    def sample_task_config(self) -> TaskConfig:
        """Create a sample task to put in our database."""
        return TaskConfig(
            task_id=uuid.uuid4(),
            task_name="test_task_config",
            client_id="demo",
            portfolio_constraints={"capex": {"max": 1e5}},
            site_constraints={"demo_london": {"capex": {"min": 1000, "max": 9999}}},
            portfolio_range={
                "demo_london": {
                    "Export_headroom": SearchSpaceEntry(min=0, max=0, step=0),
                    "Export_kWh_price": 5,
                    "Fixed_load1_scalar": SearchSpaceEntry(min=1, max=1, step=0),
                }
            },
            objectives=["capex", "carbon_balance"],
            input_data={
                "demo_london": RemoteMetaData(
                    site_id="demo_london",
                    start_ts=datetime.datetime(year=2025, month=1, day=1, tzinfo=datetime.UTC),
                    duration=DataDuration.year,
                    dataset_ids={"HeatingLoad": uuid.uuid4()},
                )
            },
            optimiser=Optimiser(name=OptimiserEnum.NSGA2, hyperparameters={}),
            created_at=datetime.datetime.now(datetime.UTC),
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
            metric_carbon_balance_scope_1=1.0,
            metric_carbon_balance_scope_2=2.0,
            metric_cost_balance=3.0,
            metric_capex=4.0,
            metric_payback_horizon=None,  # we didn't calculate this one
            metric_annualised_cost=-1.0,  # this one is negative!
        )

    @pytest.fixture
    def sample_site_optimisation_result(
        self, sample_portfolio_optimisation_result: PortfolioOptimisationResult
    ) -> SiteOptimisationResult:
        """Create a sample result for the one site in our portfolio."""
        return SiteOptimisationResult(
            portfolio_id=sample_portfolio_optimisation_result.portfolio_id,
            site_id="demo_london",
            scenario={"grid": {"foo": 1.0, "bar": 2.0}},
            metric_carbon_balance_scope_1=1.0,
            metric_carbon_balance_scope_2=2.0,
            metric_cost_balance=3.0,
            metric_capex=4.0,
            metric_payback_horizon=None,  # we didn't calculate this one
            metric_annualised_cost=-1.0,  # this one is negative!
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
        assert listed_tasks[0]["result_ids"] is None, "We should have received no result IDs"

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
            content=OptimisationResultEntry(portfolio=[sample_portfolio_optimisation_result], sites=[]).model_dump_json(),
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
            content=OptimisationResultEntry(portfolio=[sample_portfolio_optimisation_result], sites=[]).model_dump_json(),
        )
        assert opt_result.status_code == 200, opt_result.text

        get_result = await client.post(
            "/get-optimisation-results", content=json.dumps({"task_id": str(sample_task_config.task_id)})
        )
        assert get_result.status_code == 200, get_result.text
        assert len(get_result.json()) == 1
        assert get_result.json()[0]["task_id"] == str(sample_task_config.task_id)
        assert get_result.json()[0]["portfolio_id"] == str(sample_portfolio_optimisation_result.portfolio_id)
        assert get_result.json()[0]["site_results"] is None

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
        to_send = OptimisationResultEntry(
            portfolio=[sample_portfolio_optimisation_result], sites=[sample_site_optimisation_result]
        )
        opt_result = await client.post("/add-optimisation-results", content=to_send.model_dump_json())
        assert opt_result.status_code == 200, opt_result.text

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

        opt_result = await client.post(
            "/add-optimisation-results",
            content=OptimisationResultEntry(
                portfolio=[sample_portfolio_optimisation_result], sites=[sample_site_optimisation_result]
            ).model_dump_json(),
        )
        assert opt_result.status_code == 200, opt_result.text

        get_result = await client.post(
            "/get-optimisation-results", content=json.dumps({"task_id": str(sample_task_config.task_id)})
        )
        assert get_result.status_code == 200, get_result.text
        assert get_result.json()[0]["task_id"] == str(sample_task_config.task_id)
        assert get_result.json()[0]["portfolio_id"] == str(sample_portfolio_optimisation_result.portfolio_id)
        assert len(get_result.json()[0]["site_results"]) == 1
        assert get_result.json()[0]["site_results"][0]["scenario"] == sample_site_optimisation_result.model_dump()["scenario"]
        assert (
            get_result.json()[0]["site_results"][0]["metric_capex"]
            == sample_site_optimisation_result.model_dump()["metric_capex"]
        )

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

        opt_result = await client.post(
            "/add-optimisation-results",
            content=OptimisationResultEntry(
                portfolio=[sample_portfolio_optimisation_result], sites=[sample_site_optimisation_result]
            ).model_dump_json(),
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

        assert isinstance(sample_task_config.input_data["demo_london"], RemoteMetaData)
        assert (
            datetime.datetime.fromisoformat(repro_data["site_data"]["demo_london"]["start_ts"])
            == sample_task_config.input_data["demo_london"].start_ts
        )
        assert repro_data["site_data"]["demo_london"]["dataset_ids"] == {
            key: str(val) for key, val in sample_task_config.input_data["demo_london"].dataset_ids.items()
        }
        assert repro_data["task_data"] == {sample_site_optimisation_result.site_id: sample_site_optimisation_result.scenario}

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
