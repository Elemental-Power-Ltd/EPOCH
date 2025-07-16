"""Tests for uploading and parsing of PHPP files via the endpoint."""

import httpx
import pytest


class TestUploadPHPP:
    """Test that we can upload a PHPP file."""

    @pytest.mark.asyncio
    async def test_upload_phpp(self, client: httpx.AsyncClient) -> None:
        """Test that we can upload a PHPP and get a good response."""
        with open("./data/phpp/PHPP_EN_V10.3_Retford Baseline.xlsx", "rb") as fi:
            resp = await client.post(
                "/upload-phpp",
                files={
                    "file": ("PHPP_EN_V10.3_Retford Baseline.xlsx", fi, "application/vnd.ms-excel"),
                },
                data={"site_id": "demo_london"},
            )
        assert resp.status_code == 200, resp.text

    @pytest.mark.asyncio
    async def test_can_list_phpp(self, client: httpx.AsyncClient) -> None:
        """Test that we can list the PHPPs added to the database."""
        # test that there are none to start
        resp = await client.post("/list-phpp", json={"site_id": "demo_london"})
        assert resp.status_code == 200
        assert not resp.json()

        with open("./data/phpp/PHPP_EN_V10.3_Retford Baseline.xlsx", "rb") as fi:
            resp = await client.post(
                "/upload-phpp",
                files={
                    "file": ("PHPP_EN_V10.3_Retford Baseline.xlsx", fi, "application/vnd.ms-excel"),
                },
                data={"site_id": "demo_london"},
            )
        assert resp.status_code == 200, resp.text

        resp = await client.post("/list-phpp", json={"site_id": "demo_london"})
        assert resp.status_code == 200
        listed_data = resp.json()
        assert len(listed_data) == 1
        assert listed_data[0]["filename"] == "PHPP_EN_V10.3_Retford Baseline.xlsx"
