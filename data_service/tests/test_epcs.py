"""Test getting EPCs from an external API."""

# ruff: noqa: D101

import httpx
import pytest

from app.internal.energy_performance_certificate import get_cepc_by_lmk, get_dec_by_lmk


@pytest.fixture
def sample_dec_lmk() -> str:
    """Get an LMK for the DEC for 100-102 Bridge Street."""
    return "909f32973f2580c23d5a8f099a3f89d01b5fcb1a92cb8e3815bfe96e3db22acc"


@pytest.fixture
def sample_cepc_lmk() -> str:
    """Get an LMK for the CEPC for Retford Town hall."""
    return "58229799032012011615435718900594"


class TestGetCEPCs:
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_get_from_lmk(self, sample_cepc_lmk: str) -> None:
        """Test that we can get a certificate from a known LMK."""
        async with httpx.AsyncClient() as client:
            result = await get_cepc_by_lmk(sample_cepc_lmk, http_client=client)
            assert result.recommendations is not None
            assert len(result.recommendations) > 2


class TestGetDECs:
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_get_from_lmk(self, sample_dec_lmk: str) -> None:
        """Test that we can get a certificate from a known LMK."""
        async with httpx.AsyncClient() as client:
            result = await get_dec_by_lmk(sample_dec_lmk, http_client=client)
            assert result.recommendations is not None
            assert len(result.recommendations) > 2
