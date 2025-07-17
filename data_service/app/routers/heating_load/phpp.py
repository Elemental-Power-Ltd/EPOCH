"""PHPP database entry endpoints."""

import datetime
import itertools
import logging
import uuid

import pandas as pd
import pydantic
from fastapi import Form, UploadFile

from ...dependencies import DatabasePoolDep
from ...internal.thermal_model.phpp.interventions import THIRD_PARTY_INTERVENTIONS, CostedIntervention
from ...internal.thermal_model.phpp.parse_phpp import phpp_to_dataframe
from ...models.core import SiteID, dataset_id_t, site_id_t
from .router import api_router


class PhppMetadata(pydantic.BaseModel):
    """Metadata for a PHPP, including the file it came from and some non-element data that might be useful."""

    filename: str | None
    site_id: str
    internal_volume: float
    floor_area: float
    structure_id: pydantic.UUID4
    created_at: pydantic.AwareDatetime


@api_router.post("/upload-phpp")
async def upload_phpp(
    pool: DatabasePoolDep,
    file: UploadFile,
    site_id: site_id_t = Form(...),  # noqa: B008
) -> PhppMetadata:
    """
    Add a PHPP file to the database.

    This will take in a valid PHPP survey and calculations, and import them into our database.
    It specifically requires PHPP v10.3 outputs.

    Parameters
    ----------
    pool
        Database connection pool to upload the PHPP to
    file
        Uploaded PHPP file (may be big, often 10-15MB)
    site_id
        The ID of the site you want to link this to. Note that this is a site_id_t and not a full nested SiteID
        due to form processing weirdness.

    Returns
    -------
    PhppMetadata
        ???
    """
    logger = logging.getLogger(__name__)
    parsed_df, structure_info = phpp_to_dataframe(file.file)
    assert not parsed_df.empty, "Parsed an empty PHPP file"
    metadata = PhppMetadata(
        filename=file.filename,
        site_id=site_id,
        internal_volume=structure_info["internal_volume"],
        floor_area=structure_info["floor_area"],
        structure_id=uuid.uuid4(),
        created_at=datetime.datetime.now(datetime.UTC),
    )
    logger.info("Adding parsed PHPP to database", str(metadata.model_dump_json()))
    async with pool.acquire() as conn:
        # Insert the metadata and the records as part of a transaction so
        # they don't slip if something goes wrong
        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO heating.structure_metadata (
                    structure_id,
                    site_id,
                    internal_volume,
                    floor_area,
                    filename,
                    created_at) VALUES ($1, $2, $3, $4, $5, $6)""",
                metadata.structure_id,
                metadata.site_id,
                metadata.internal_volume,
                metadata.floor_area,
                metadata.filename,
                metadata.created_at,
            )

            await conn.copy_records_to_table(
                schema_name="heating",
                table_name="structure_elements",
                columns=[
                    "structure_id",
                    "element_id",
                    "element_name",
                    "element_group",
                    "area",
                    "angle",
                    "u_value",
                    "area_type",
                ],
                records=zip(
                    itertools.repeat(metadata.structure_id, len(parsed_df)),
                    parsed_df.index,
                    parsed_df.name,
                    parsed_df.group,
                    [item if not pd.isna(item) else None for item in parsed_df.area],
                    [item if not pd.isna(item) else None for item in parsed_df.angle],
                    [item if not pd.isna(item) else None for item in parsed_df.u_value],
                    parsed_df.area_type,
                    strict=True,
                ),
            )
    return metadata


@api_router.post("/list-phpp")
async def list_phpp(pool: DatabasePoolDep, site_id: SiteID) -> list[PhppMetadata]:
    """
    List all the PHPPs we have available for a given site.

    Parameters
    ----------
    pool
        Connection pool to the database to search in
    site_id
        Database ID of the site to check

    Returns
    -------
    list[PhppMetadata]
        List of the created PHPPs for this site
    """
    logger = logging.getLogger(__name__)
    records = await pool.fetch(
        """
         SELECT
            structure_id,
            internal_volume,
            floor_area,
            filename,
            created_at
        FROM heating.structure_metadata
        WHERE site_id = $1
        ORDER BY created_at DESC""",
        site_id.site_id,
    )

    if not records:
        logger.info(f"Found no PHPPs for {site_id.site_id} in the database")
        return []
    return [
        PhppMetadata(
            filename=item["filename"],
            site_id=site_id.site_id,
            internal_volume=item["internal_volume"],
            floor_area=item["floor_area"],
            structure_id=item["structure_id"],
            created_at=item["created_at"],
        )
        for item in records
    ]


async def get_phpp_dataframe_from_database(
    pool: DatabasePoolDep, structure_id: dataset_id_t
) -> tuple[pd.DataFrame, PhppMetadata]:
    """
    Get a PHPP from the database and some metadata.

    TODO: tidy up the return type.
    """
    records = await pool.fetch(
        """
        SELECT
            element_id,
            element_name,
            element_group,
            area,
            angle,
            u_value,
            area_type
        FROM heating.structure_elements
        WHERE structure_id = $1
        ORDER BY element_id ASC""",
        structure_id,
    )

    metadata = await pool.fetchrow(
        """
        SELECT
            site_id,
            structure_id,
            internal_volume,
            floor_area,
            filename,
            created_at
        FROM heating.structure_metadata
        WHERE structure_id = $1
        LIMIT 1""",
        structure_id,
    )
    assert metadata is not None, "Got None metadata"
    return pd.DataFrame.from_records(dict(item) for item in records), PhppMetadata(
        filename=metadata["filename"],
        site_id=metadata["site_id"],
        internal_volume=metadata["internal_volume"],
        floor_area=metadata["floor_area"],
        structure_id=metadata["structure_id"],
        created_at=metadata["created_at"],
    )


@api_router.post("/list-interventions")
async def list_interventions() -> dict[str, CostedIntervention]:
    """
    List the available fabric interventions, including their cost and what areas they affect.

    This is a hard-coded list in the python code, but may change to a database lookup in future.
    An intervention has a name, which you can pass to other PHPP heat load endpoints,
    a cost in £/m^2, an affected area e.g. windows or walls, and a new U-value for those areas.

    Parameters
    ----------
    None

    Returns
    -------
    dict[str, CostedIntervention]
        Dictionary keyed by intervention name with details in the values
    """
    return THIRD_PARTY_INTERVENTIONS
