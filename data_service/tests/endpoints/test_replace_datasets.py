"""Test that we can replace datasets with the replacement endpoint."""

import datetime
import tempfile

import pandas as pd
import pytest
from app.internal.site_manager.bundles import file_self_with_bundle, insert_dataset_bundle
from app.internal.utils.uuid import uuid7
from app.models.core import BundleEntryMetadata, DatasetTypeEnum
from app.models.site_manager import DatasetBundleMetadata
from httpx import AsyncClient

from .conftest import get_pool_hack


class TestReplaceDatasets:
    """Test dataset replacement through the main endpoint."""

    @pytest.mark.asyncio
    async def test_can_replace_solar(self, client: AsyncClient) -> None:
        """Test that we can replace a solar dataframe in the database."""
        pool = await get_pool_hack(client)

        old_dataset_id = uuid7()

        bundle_meta = BundleEntryMetadata(
            bundle_id=uuid7(), dataset_id=old_dataset_id, dataset_type=DatasetTypeEnum.RenewablesGeneration
        )
        start_ts = pd.Timestamp(year=2022, month=1, day=1, tzinfo=datetime.UTC)
        old_df = pd.DataFrame(
            index=pd.date_range(start_ts, end=start_ts + pd.Timedelta(hours=365 * 24), freq=pd.Timedelta(hours=1)),
            data={"solar_pv": [0.0 for _ in range(365 * 24)]},
        )

        # First we create our fake renewables dataframe
        async with pool.acquire() as conn, conn.transaction():
            await insert_dataset_bundle(
                DatasetBundleMetadata(
                    bundle_id=bundle_meta.bundle_id,
                    name="Test Replace Solar",
                    site_id="demo_london",
                    start_ts=old_df.index.min(),
                    end_ts=old_df.index.max(),
                ),
                pool=pool,
            )
            await conn.execute(
                """
                    INSERT INTO
                        renewables.metadata (
                            dataset_id,
                            site_id,
                            created_at,
                            data_source,
                            parameters)
                    VALUES (
                            $1,
                            $2,
                            $3,
                            $4,
                            $5)""",
                old_dataset_id,
                "demo_london",
                datetime.datetime.now(datetime.UTC),
                "testing",
                None,
            )

            await conn.executemany(
                """INSERT INTO
                            renewables.solar_pv (
                                dataset_id,
                                start_ts,
                                end_ts,
                                solar_generation
                            )
                        VALUES (
                            $1,
                            $2,
                            $3,
                            $4)""",
                zip(
                    [old_dataset_id for _ in old_df.index],
                    old_df.index,
                    old_df.index + pd.Timedelta(hours=1),
                    old_df["solar_pv"],
                    strict=True,
                ),
            )
            await file_self_with_bundle(pool, bundle_meta)

        with tempfile.TemporaryFile() as tfile:
            new_df = pd.DataFrame(
                index=pd.date_range(start_ts, end=start_ts + pd.Timedelta(hours=365 * 24 * 2), freq=pd.Timedelta(minutes=30)),
                data={"solar_pv": [1.0 for _ in range(365 * 24 * 2)]},
            )
            new_df["start_ts"] = new_df.index
            new_df["end_ts"] = new_df.index + pd.Timedelta(minutes=30)

            new_df.to_csv(tfile, index=False)

            resp = await client.post(
                "/replace-dataset",
                params={"dataset_id": str(old_dataset_id)},
                files={"data": (str(tfile.name), tfile, "text/csv")},
            )
            assert resp.is_success, resp.text
            assert resp.json()["dataset_id"] != str(old_dataset_id)

            resp = await client.post("/get-dataset-bundle", params={"bundle_id": str(bundle_meta.bundle_id)})
            assert resp.is_success, resp.text
            data = resp.json()["rgen"]["data"][0]
            assert all(item == 1.0 for item in data)
