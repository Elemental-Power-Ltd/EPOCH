import datetime

import pytest
from fastapi.encoders import jsonable_encoder
from httpx import AsyncClient

from app.internal.database.site_data import get_latest_bundle_metadata
from app.models.core import Site
from app.models.epoch_types.site_range_type import Config, SiteRange
from app.models.merge import PortfolioMergeRequest, SiteInfo
from app.models.result import SiteSolution
from app.routers.merge import merge_site_scenarios_into_portfolios

from .conftest import get_internal_client_hack


class TestMergeSiteScenariosIntoPortfoliosAndTransmit:
    """Test the merge_site_scenarios_into_portfolios_and_transmit method."""

    @pytest.mark.asyncio
    async def test_good_inputs(
        self, client: AsyncClient, default_portfolio: list[Site], dummy_site_solution: SiteSolution
    ) -> None:
        site_ids = [site.site_data.site_id for site in default_portfolio]

        http_client = get_internal_client_hack(client)
        start_ts = datetime.datetime(year=2022, month=1, day=1, hour=0).astimezone(datetime.UTC)
        end_ts = datetime.datetime(year=2023, month=1, day=1, hour=0).astimezone(datetime.UTC)

        site_scenario_list = [dummy_site_solution.scenario, dummy_site_solution.scenario]

        sites = []
        for site_id in site_ids:
            bundle_metadata = await get_latest_bundle_metadata(
                site_id=site_id, start_ts=start_ts, end_ts=end_ts, http_client=http_client
            )

            site = SiteInfo(
                site_id=site_id,
                bundle_id=bundle_metadata.bundle_id,
                scenarios=site_scenario_list,
                constraints={},
                site_range=SiteRange(config=Config()),
            )
            sites.append(site)

        data = PortfolioMergeRequest(sites=sites, client_id="demo", task_name="test_merging")
        response = await client.post("/merge-site-scenarios", json=jsonable_encoder(data))
        assert response.is_success, response.text


class TestMergeSiteScenariosIntoPortfolios:
    """Test the merge_site_scenarios_into_portfolios method."""

    @pytest.mark.asyncio
    async def test_good_inputs(
        self, client: AsyncClient, dummy_site_solution: SiteSolution, default_portfolio: list[Site]
    ) -> None:
        """Test method works with good inputs."""
        start_ts = datetime.datetime(year=2022, month=1, day=1, hour=0).astimezone(datetime.UTC)
        end_ts = datetime.datetime(year=2023, month=1, day=1, hour=0).astimezone(datetime.UTC)

        http_client = get_internal_client_hack(client)

        site_ids = [site.site_data.site_id for site in default_portfolio]

        bundle_ids = {}
        for site_id in site_ids:
            bundle_metadata = await get_latest_bundle_metadata(
                site_id=site_id, start_ts=start_ts, end_ts=end_ts, http_client=http_client
            )
            bundle_ids[site_id] = bundle_metadata.bundle_id

        site_scenario_list = [dummy_site_solution.scenario, dummy_site_solution.scenario]
        site_scenario_lists = dict.fromkeys(site_ids, site_scenario_list)
        configs = dict.fromkeys(site_ids, Config())

        portfolio_solutions = await merge_site_scenarios_into_portfolios(
            site_scenario_lists=site_scenario_lists, bundle_ids=bundle_ids, configs=configs, http_client=http_client
        )

        assert len(portfolio_solutions) == len(site_scenario_list)
        for single, double in zip(site_scenario_list, portfolio_solutions, strict=False):
            for site_id in site_ids:
                assert single == double.scenario[site_id].scenario

    @pytest.mark.asyncio
    async def test_mismatched_scenario_lengths(
        self, client: AsyncClient, dummy_site_solution: SiteSolution, default_portfolio: list[Site]
    ) -> None:
        """Test method raises a ValueError if the site scenario lists aren't of the same length."""
        start_ts = datetime.datetime(year=2022, month=1, day=1, hour=0).astimezone(datetime.UTC)
        end_ts = datetime.datetime(year=2023, month=1, day=1, hour=0).astimezone(datetime.UTC)

        http_client = get_internal_client_hack(client)

        site_ids = [site.site_data.site_id for site in default_portfolio]

        bundle_ids = {}
        for site_id in site_ids:
            bundle_metadata = await get_latest_bundle_metadata(
                site_id=site_id, start_ts=start_ts, end_ts=end_ts, http_client=http_client
            )
            bundle_ids[site_id] = bundle_metadata.bundle_id

        site_scenario_list = [dummy_site_solution.scenario, dummy_site_solution.scenario]
        site_scenario_lists = dict.fromkeys(site_ids, site_scenario_list)
        site_scenario_lists[site_ids[0]] = [dummy_site_solution.scenario]

        configs = dict.fromkeys(site_ids, Config())

        with pytest.raises(ValueError):
            await merge_site_scenarios_into_portfolios(
                site_scenario_lists=site_scenario_lists, bundle_ids=bundle_ids, configs=configs, http_client=http_client
            )

    @pytest.mark.asyncio
    async def test_mismatched_indexes(
        self, client: AsyncClient, dummy_site_solution: SiteSolution, default_portfolio: list[Site]
    ) -> None:
        """Test method raises a ValueError if the inputs aren't indexed on the same site_ids."""
        start_ts = datetime.datetime(year=2022, month=1, day=1, hour=0).astimezone(datetime.UTC)
        end_ts = datetime.datetime(year=2023, month=1, day=1, hour=0).astimezone(datetime.UTC)

        http_client = get_internal_client_hack(client)

        site_ids = [site.site_data.site_id for site in default_portfolio]

        bundle_ids = {}
        for site_id in site_ids:
            bundle_metadata = await get_latest_bundle_metadata(
                site_id=site_id, start_ts=start_ts, end_ts=end_ts, http_client=http_client
            )
            bundle_ids[site_id] = bundle_metadata.bundle_id

        site_scenario_list = [dummy_site_solution.scenario, dummy_site_solution.scenario]
        site_scenario_lists = dict.fromkeys(site_ids, site_scenario_list)
        site_scenario_lists[site_ids[0]] = [dummy_site_solution.scenario]

        configs = {"tree": Config()}

        with pytest.raises(ValueError):
            await merge_site_scenarios_into_portfolios(
                site_scenario_lists=site_scenario_lists, bundle_ids=bundle_ids, configs=configs, http_client=http_client
            )
