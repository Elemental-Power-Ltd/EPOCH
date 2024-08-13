import pytest
import httpx

class TestHeatingLoad:
    @pytest.mark.asyncio
    async def test_generate_heating_load(self, client: httpx.AsyncClient) -> None:
        datasets = (await client.post("/list-latest-datasets", json={"site_id": "demo_london"})).json()
        print(datasets)
        assert datasets
        assert False