"""
Useful functions for site data, including postcode extraction.

Author: Matt Bailey
"""

import asyncpg


async def get_postcode(site_id: str, pool: asyncpg.pool.Pool) -> str:
    """
    Get the postcode of a given site.

    The postcode is stored in the address field in the database, so use a hideous regular expression to extract it.

    Parameters
    ----------
    site_id
        Database ID of the site you're interested in
    pool
        Database connection pool

    Returns
    -------
    Postcode
        Both incoming and outgoing sections
    """
    result = await pool.fetchval(
        r"""
    SELECT
        (regexp_match(address, '[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}'))[1]
    FROM client_info.site_info
    WHERE site_id = $1""",
        site_id,
    )
    if result is None:
        raise ValueError(f"Got a None postcode for {site_id}.")
    return str(result)
