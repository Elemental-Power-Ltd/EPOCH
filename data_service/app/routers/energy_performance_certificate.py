"""Endpoint to get energy performance certificates for a given site."""

from fastapi import APIRouter

from app.dependencies import DatabasePoolDep, HttpClientDep
from app.internal.energy_performance_certificate import get_cepc_by_lmk, get_dec_by_lmk
from app.models.core import SiteID
from app.models.energy_performance_certificate import CertificateType, NonDomesticDEC, NonDomesticEPC

from .client_data import get_site_data

router = APIRouter()


@router.post("/get-epcs")
async def get_epc(
    site_id: SiteID, pool: DatabasePoolDep, http_client: HttpClientDep
) -> dict[CertificateType, NonDomesticDEC | NonDomesticEPC | None]:
    """
    Get the Energy Performance Certificates for this site.

    This presumes that you have pre-filled the relevant epc_lmk and dec_lmk fields in the database for the site,
    and that those certificates still exist in the external API.
    Note that we do not store the certificates, so we have to get them fresh each time.

    Parameters
    ----------
    site_id
        ID of the site you want to look up EPCs for
    pool
        Database pool connection to look up site metadata
    http_client
        HTTP client to request data from the EPC database

    Returns
    -------
    dict[CertificateType, NonDomesticDEC | NonDomesticEPC | None]
        Dict with the different certificate types, or None if they do not exist (or your dec_lmk is None)
    """
    site_data = await get_site_data(site_id, pool)

    if site_data.epc_lmk is not None:
        epc = await get_cepc_by_lmk(site_data.epc_lmk, http_client=http_client)
    else:
        epc = None

    if site_data.dec_lmk is not None:
        dec = await get_dec_by_lmk(site_data.dec_lmk, http_client=http_client)
    else:
        dec = None

    return {CertificateType.NonDomesticEPC: epc, CertificateType.NonDomesticDEC: dec}
