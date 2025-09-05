import pytest
from httpx import AsyncClient


class TestMain:
    @pytest.mark.asyncio
    async def test_read_main(self, client: AsyncClient) -> None:
        """
        Test server.
        """
        response = await client.get("/")
        assert response.status_code == 200
