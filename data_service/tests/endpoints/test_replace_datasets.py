"""Test that we can replace datasets with the replacement endpoint."""

import datetime
import tempfile
from itertools import repeat

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
            index=pd.date_range(
                start_ts, end=start_ts + pd.Timedelta(hours=365 * 24), freq=pd.Timedelta(hours=1), inclusive="left"
            ),
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
                index=pd.date_range(
                    start_ts, end=start_ts + pd.Timedelta(hours=365 * 24), freq=pd.Timedelta(minutes=30), inclusive="left"
                ),
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

    @pytest.mark.asyncio
    async def test_can_replace_heating(self, client: AsyncClient) -> None:
        """Test that we can replace a heating load dataframe in the database."""
        pool = await get_pool_hack(client)

        old_dataset_id = uuid7()

        bundle_meta = BundleEntryMetadata(
            bundle_id=uuid7(), dataset_id=old_dataset_id, dataset_type=DatasetTypeEnum.HeatingLoad
        )
        start_ts = pd.Timestamp(year=2022, month=1, day=1, tzinfo=datetime.UTC)
        heating_df = pd.DataFrame(
            index=pd.date_range(
                start_ts, end=start_ts + pd.Timedelta(hours=365 * 24), freq=pd.Timedelta(minutes=30), inclusive="left"
            ),
            data={
                "heating": [0.0 for _ in range(365 * 24 * 2)],
                "dhw": [0.0 for _ in range(365 * 24 * 2)],
                "air_temperature": [0.0 for _ in range(365 * 24 * 2)],
            },
        )

        heating_df["start_ts"] = heating_df.index
        heating_df["end_ts"] = heating_df.index + pd.Timedelta(minutes=30)

        # First we create our fake renewables dataframe
        async with pool.acquire() as conn, conn.transaction():
            await insert_dataset_bundle(
                DatasetBundleMetadata(
                    bundle_id=bundle_meta.bundle_id,
                    name="Test Replace Heating",
                    site_id="demo_london",
                    start_ts=heating_df.index.min(),
                    end_ts=heating_df.index.max(),
                ),
                pool=pool,
            )
            await conn.execute(
                """
                INSERT INTO
                    heating.metadata (
                        dataset_id,
                        site_id,
                        created_at,
                        params,
                        interventions,
                        fabric_cost_total,
                        fabric_cost_breakdown
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                old_dataset_id,
                "demo_london",
                datetime.datetime.now(datetime.UTC),
                None,
                [],
                0.0,
                None,
            )

            await conn.copy_records_to_table(
                schema_name="heating",
                table_name="synthesised",
                columns=["dataset_id", "start_ts", "end_ts", "heating", "dhw", "air_temperature"],
                records=zip(
                    repeat(old_dataset_id, len(heating_df)),
                    heating_df["start_ts"],
                    heating_df["end_ts"],
                    heating_df["heating"],
                    heating_df["dhw"],
                    heating_df["air_temperature"],
                    strict=True,
                ),
            )
            await file_self_with_bundle(pool, bundle_meta)

        with tempfile.TemporaryFile() as tfile:
            new_df = pd.DataFrame(
                index=pd.date_range(
                    start_ts, end=start_ts + pd.Timedelta(hours=365 * 24), freq=pd.Timedelta(minutes=30), inclusive="left"
                ),
                data={
                    "heating": [1.0 for _ in range(365 * 24 * 2)],
                    "dhw": [2.0 for _ in range(365 * 24 * 2)],
                    "air_temperature": [3.0 for _ in range(365 * 24 * 2)],
                },
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

            heating = resp.json()["heat"]["data"][0]["reduced_hload"]
            assert all(item == 1.0 for item in heating)

            dhw = resp.json()["dhw"]["data"]
            assert all(item == 2.0 for item in dhw)

            air_temp = resp.json()["air_temp"]["data"]
            assert all(item == 3.0 for item in air_temp)

    @pytest.mark.asyncio
    async def test_cant_replace_heating_no_dhw(self, client: AsyncClient) -> None:
        """Test that we can't replace a heating dataset if we're missing a column."""
        pool = await get_pool_hack(client)

        old_dataset_id = uuid7()

        bundle_meta = BundleEntryMetadata(
            bundle_id=uuid7(), dataset_id=old_dataset_id, dataset_type=DatasetTypeEnum.HeatingLoad
        )
        start_ts = pd.Timestamp(year=2022, month=1, day=1, tzinfo=datetime.UTC)
        heating_df = pd.DataFrame(
            index=pd.date_range(
                start_ts, end=start_ts + pd.Timedelta(hours=365 * 24), freq=pd.Timedelta(minutes=30), inclusive="left"
            ),
            data={
                "heating": [0.0 for _ in range(365 * 24 * 2)],
                "dhw": [0.0 for _ in range(365 * 24 * 2)],
                "air_temperature": [0.0 for _ in range(365 * 24 * 2)],
            },
        )

        heating_df["start_ts"] = heating_df.index
        heating_df["end_ts"] = heating_df.index + pd.Timedelta(minutes=30)

        # First we create our fake renewables dataframe
        async with pool.acquire() as conn, conn.transaction():
            await insert_dataset_bundle(
                DatasetBundleMetadata(
                    bundle_id=bundle_meta.bundle_id,
                    name="Test Replace Heating",
                    site_id="demo_london",
                    start_ts=heating_df.index.min(),
                    end_ts=heating_df.index.max(),
                ),
                pool=pool,
            )
            await conn.execute(
                """
                INSERT INTO
                    heating.metadata (
                        dataset_id,
                        site_id,
                        created_at,
                        params,
                        interventions,
                        fabric_cost_total,
                        fabric_cost_breakdown
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                old_dataset_id,
                "demo_london",
                datetime.datetime.now(datetime.UTC),
                None,
                [],
                0.0,
                None,
            )

            await conn.copy_records_to_table(
                schema_name="heating",
                table_name="synthesised",
                columns=["dataset_id", "start_ts", "end_ts", "heating", "dhw", "air_temperature"],
                records=zip(
                    repeat(old_dataset_id, len(heating_df)),
                    heating_df["start_ts"],
                    heating_df["end_ts"],
                    heating_df["heating"],
                    heating_df["dhw"],
                    heating_df["air_temperature"],
                    strict=True,
                ),
            )
            await file_self_with_bundle(pool, bundle_meta)

        with tempfile.TemporaryFile() as tfile:
            new_df = pd.DataFrame(
                index=pd.date_range(
                    start_ts, end=start_ts + pd.Timedelta(hours=365 * 24), freq=pd.Timedelta(minutes=30), inclusive="left"
                ),
                data={
                    "heating": [1.0 for _ in range(365 * 24 * 2)],
                    # NO DHW COLUMN,
                    "air_temperature": [3.0 for _ in range(365 * 24 * 2)],
                },
            )
            new_df["start_ts"] = new_df.index
            new_df["end_ts"] = new_df.index + pd.Timedelta(minutes=30)

            new_df.to_csv(tfile, index=False)

            resp = await client.post(
                "/replace-dataset",
                params={"dataset_id": str(old_dataset_id)},
                files={"data": (str(tfile.name), tfile, "text/csv")},
            )
            assert resp.status_code == 422, "dhw" in resp.text

    @pytest.mark.asyncio
    async def test_can_replace_import_tariffs(self, client: AsyncClient) -> None:
        """Test that we can replace an import tariff dataframe in the database."""
        pool = await get_pool_hack(client)

        old_dataset_id = uuid7()

        bundle_meta = BundleEntryMetadata(
            bundle_id=uuid7(), dataset_id=old_dataset_id, dataset_type=DatasetTypeEnum.ImportTariff
        )
        start_ts = pd.Timestamp(year=2022, month=1, day=1, tzinfo=datetime.UTC)
        price_df = pd.DataFrame(
            index=pd.date_range(
                start_ts, end=start_ts + pd.Timedelta(hours=365 * 24), freq=pd.Timedelta(hours=1), inclusive="left"
            ),
            data={"unit_cost": [0.0 for _ in range(365 * 24)]},
        )
        price_df["start_ts"] = price_df.index
        price_df["end_ts"] = price_df.index + pd.Timedelta(minutes=30)
        # First we create our fake renewables dataframe
        async with pool.acquire() as conn, conn.transaction():
            await conn.execute("SET CONSTRAINTS tariffs.electricity_dataset_id_metadata_fkey DEFERRED;")
            await insert_dataset_bundle(
                DatasetBundleMetadata(
                    bundle_id=bundle_meta.bundle_id,
                    name="Test Replace Tariffs",
                    site_id="demo_london",
                    start_ts=price_df.index.min(),
                    end_ts=price_df.index.max(),
                ),
                pool=pool,
            )
            # We insert the dataset ID into metadata, but we must wait to validate the
            # actual data insert until the end

            await conn.execute(
                """
                    INSERT INTO
                        tariffs.metadata (
                            dataset_id,
                            site_id,
                            created_at,
                            provider,
                            product_name,
                            tariff_name,
                            valid_from,
                            valid_to)
                    VALUES (
                            $1,
                            $2,
                            $3,
                            $4,
                            $5,
                            $6,
                            $7,
                            $8)""",
                old_dataset_id,
                "demo_london",
                datetime.datetime.now(datetime.UTC),
                "custom",
                "custom",
                "custom",
                None,
                None,
            )

            await conn.copy_records_to_table(
                table_name="electricity",
                schema_name="tariffs",
                records=zip(
                    repeat(old_dataset_id, len(price_df)),
                    price_df["start_ts"],
                    price_df["end_ts"],
                    price_df["unit_cost"],
                    strict=True,
                ),
                columns=["dataset_id", "start_ts", "end_ts", "unit_cost"],
            )
            await file_self_with_bundle(pool, bundle_meta)

        with tempfile.TemporaryFile() as tfile:
            new_df = pd.DataFrame(
                index=pd.date_range(
                    start_ts, end=start_ts + pd.Timedelta(hours=365 * 24), freq=pd.Timedelta(minutes=30), inclusive="left"
                ),
                data={"unit_cost": [1.0 for _ in range(365 * 24 * 2)]},
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
            data = resp.json()["import_tariffs"]["data"][0]
            # curse this design decision
            assert all(item == 0.01 for item in data), "Watch out for a factor of /100!"

    @pytest.mark.asyncio
    async def test_can_replace_eload(self, client: AsyncClient) -> None:
        """Test that we can replace an  eletrical load dataframe in the database."""
        pool = await get_pool_hack(client)

        old_dataset_id = uuid7()

        bundle_meta = BundleEntryMetadata(
            bundle_id=uuid7(), dataset_id=old_dataset_id, dataset_type=DatasetTypeEnum.ElectricityMeterDataSynthesised
        )
        start_ts = pd.Timestamp(year=2022, month=1, day=1, tzinfo=datetime.UTC)
        synthetic_hh_df = pd.DataFrame(
            index=pd.date_range(
                start_ts, end=start_ts + pd.Timedelta(hours=365 * 24), freq=pd.Timedelta(hours=1), inclusive="left"
            ),
            data={"consumption_kwh": [0.0 for _ in range(365 * 24)]},
        )
        synthetic_hh_df["start_ts"] = synthetic_hh_df.index
        synthetic_hh_df["end_ts"] = synthetic_hh_df.index + pd.Timedelta(minutes=30)
        # First we create our fake renewables dataframe
        async with pool.acquire() as conn, conn.transaction():
            await insert_dataset_bundle(
                DatasetBundleMetadata(
                    bundle_id=bundle_meta.bundle_id,
                    name="Test Replace Elec Load",
                    site_id="demo_london",
                    start_ts=synthetic_hh_df.index.min(),
                    end_ts=synthetic_hh_df.index.max(),
                ),
                pool=pool,
            )
            await conn.execute(
                """
                INSERT INTO
                    client_meters.metadata (
                        dataset_id,
                        site_id,
                        created_at,
                        fuel_type,
                        reading_type,
                        filename,
                        is_synthesised)
                VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                old_dataset_id,
                "demo_london",
                datetime.datetime.now(datetime.UTC),
                "elec",
                "halfhourly",
                "fake.csv",
                True,
            )
            await conn.copy_records_to_table(
                table_name="electricity_meters_synthesised",
                schema_name="client_meters",
                records=zip(
                    repeat(old_dataset_id, len(synthetic_hh_df)),
                    synthetic_hh_df["start_ts"],
                    synthetic_hh_df["end_ts"],
                    synthetic_hh_df["consumption_kwh"],
                    strict=True,
                ),
                columns=["dataset_id", "start_ts", "end_ts", "consumption_kwh"],
            )
            await file_self_with_bundle(pool, bundle_meta)

        with tempfile.TemporaryFile() as tfile:
            new_df = pd.DataFrame(
                index=pd.date_range(
                    start_ts, end=start_ts + pd.Timedelta(hours=365 * 24), freq=pd.Timedelta(minutes=30), inclusive="left"
                ),
                data={"consumption_kwh": [1.0 for _ in range(365 * 24 * 2)]},
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
            data = resp.json()["eload"]["data"]
            # curse this design decision
            assert all(item == 1.00 for item in data)
