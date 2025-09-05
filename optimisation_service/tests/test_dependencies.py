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

        async def mock_post(*args: Any, **kwargs: Any) -> httpx.Response:
            return fake_response

        mock_post = mocker.patch("httpx.AsyncClient.post", side_effect=mock_post)

        client = CachedAsyncClient()

        response = await client.post(url=_DB_URL + "/get-dataset-bundle", params={"bundle_id": str(123)})

        assert response == fake_response
        assert mock_post.call_count == 1

        response = await client.post(url=_DB_URL + "/get-dataset-bundle", params={"bundle_id": str(123)})

        assert response == fake_response
        assert mock_post.call_count == 1

        response = await client.post(url=_DB_URL + "/get-dataset-bundle", params={"bundle_id": str(321)})

        assert response == fake_response
        assert mock_post.call_count == 2
