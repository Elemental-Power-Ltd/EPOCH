import asyncio
import time
from typing import Any

import httpx
import pytest
from pytest_mock import MockerFixture

from app.dependencies import CachedAsyncClient
from app.internal.database.utils import _DB_URL


class TestCachedAsyncClient:
    @pytest.mark.asyncio
    async def test_bundle_caching(self, mocker: MockerFixture) -> None:
        """Test that post requests to "/get-dataset-bundle" get cached by the client."""
        fake_response = httpx.Response(200, json={"ok": True})

        mock_post_delay = 10

        async def delayed_post(*args: Any, **kwargs: Any) -> httpx.Response:
            await asyncio.sleep(mock_post_delay)
            return fake_response

        mocker.patch("httpx.AsyncClient.post", side_effect=delayed_post)

        client = CachedAsyncClient()

        start_time = time.perf_counter()
        response = await client.post(url=_DB_URL + "/get-dataset-bundle")
        end_time = time.perf_counter()

        elapsed = end_time - start_time

        assert response == fake_response
        assert mock_post_delay <= elapsed, f"Post request took {elapsed:.2f} seconds, expected at least {mock_post_delay}"

        start_time = time.perf_counter()
        response = await client.post(url=_DB_URL + "/get-dataset-bundle")
        end_time = time.perf_counter()

        elapsed = end_time - start_time

        assert response == fake_response
        assert elapsed < 1, f"Post request took {elapsed:.2f} seconds, expected less than {1}"
