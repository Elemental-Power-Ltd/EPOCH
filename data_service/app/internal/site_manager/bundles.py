"""Minor functions for bundle handling."""

import json

from ...models.core import BundleEntryMetadata, dataset_id_t
from ...models.site_manager import DatasetBundleMetadata
from ..epl_typing import db_conn_t


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
        json.dumps(bundle_metadata.dataset_subtype) if bundle_metadata.dataset_subtype is not None else None,
        bundle_metadata.dataset_id,
        bundle_metadata.dataset_order,
    )


async def insert_dataset_bundle(bundle_metadata: DatasetBundleMetadata, pool: db_conn_t) -> dataset_id_t:
    """
    Insert metadata about a dataset bundle into the database.

    A dataset bundle is a collection of datasets applying to the same site, created at the same time.
    This will generally include heating loads, electrical loads, carbon intensity, renewables etc.
    There is no guarantee that a given bundle is complete.
    Bundles are stored in a top level metadata table showing which sites they are for, and a below dataset links table.
    This only inserts that top level metadata, and the associated datasets will file themselves via
    `file_self_with_bundle` (note that this means a given bundle can change over time, or be empty)

    Parameters
    ----------
    bundle_metadata
        Dataset bundle metadata, including site ID, human readable name, and start / end times.
    pool
        Connection pool to the database that we want these to be filed in

    Returns
    -------
    dataset_id_t
        The bundle ID for this bundle of datasets, in case you want it later.
    """
    await pool.execute(
        """
        INSERT INTO data_bundles.metadata (
            bundle_id,
            name,
            site_id,
            start_ts,
            end_ts,
            created_at
        ) VALUES ($1, $2, $3, $4, $5, $6)""",
        bundle_metadata.bundle_id,
        bundle_metadata.name,
        bundle_metadata.site_id,
        bundle_metadata.start_ts,
        bundle_metadata.end_ts,
        bundle_metadata.created_at,
    )
    return bundle_metadata.bundle_id
