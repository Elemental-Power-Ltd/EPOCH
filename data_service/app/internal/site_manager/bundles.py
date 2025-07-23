"""Minor functions for bundle handling."""

import json

import asyncpg

from ...models.core import BundleEntryMetadata

type db_conn_t = asyncpg.pool.Pool | asyncpg.Connection | asyncpg.pool.PoolConnectionProxy


async def file_self_with_bundle(pool: db_conn_t, bundle_metadata: BundleEntryMetadata) -> None:
    """
    File the completed generation of a dataset generation task with the database.

    This should be called at the end of any given process that creates a dataset which might be part of a bundle.

    Parameters
    ----------
    pool
        Database connection pool to file the metadata in, or individual connection if you've already got one
    bundle_metadata
        Metadata about this entry, including the associated bundle ID, the dataset ID and the types.

    Returns
    -------
    None
        You'll just have to hope it completed successfully
    """
    await pool.execute(
        """
        INSERT INTO data_bundles.dataset_links (
            bundle_id,
            dataset_type,
            dataset_subtype,
            dataset_id,
            dataset_order
        ) VALUES ($1, $2, $3, $4, $5);""",
        bundle_metadata.bundle_id,
        bundle_metadata.dataset_type,
        json.dumps(bundle_metadata.dataset_subtype),
        bundle_metadata.dataset_id,
        bundle_metadata.dataset_order,
    )
