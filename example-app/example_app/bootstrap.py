from iceaxe import DBConnection, select
from iceaxe.schemas.cli import create_all
from iceaxe.schemas.db_memory_serializer import DatabaseMemorySerializer
from iceaxe.schemas.db_stubs import DBTable, DBType

from example_app import models
from example_app.constants import DEFAULT_DETAIL_DESCRIPTION


def _managed_schema_names() -> tuple[frozenset[str], frozenset[str]]:
    db_objects = [
        obj
        for obj, _ in DatabaseMemorySerializer().delegate(
            [models.User, models.VerificationState, models.DetailItem]
        )
    ]
    return (
        frozenset(
            obj.table_name for obj in db_objects if isinstance(obj, DBTable)
        ),
        frozenset(obj.name for obj in db_objects if isinstance(obj, DBType)),
    )


async def bootstrap_database(db_connection: DBConnection) -> None:
    managed_tables, managed_types = _managed_schema_names()
    existing_tables = {
        row["table_name"]
        for row in await db_connection.conn.fetch(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            """
        )
    }
    existing_types = {
        row["typname"]
        for row in await db_connection.conn.fetch(
            """
            SELECT typname
            FROM pg_type
            WHERE typtype = 'e'
                AND typnamespace = (
                    SELECT oid FROM pg_namespace WHERE nspname = 'public'
                )
            """
        )
    }

    present_tables = managed_tables & existing_tables
    present_types = managed_types & existing_types

    if not present_tables and not present_types:
        await create_all(db_connection=db_connection)
    elif present_tables != managed_tables or present_types != managed_types:
        raise RuntimeError(
            "Example app schema is partially initialized. "
            f"Found tables={sorted(present_tables)} and types={sorted(present_types)}, "
            f"expected tables={sorted(managed_tables)} and types={sorted(managed_types)}. "
            "Reset the database or apply migrations before restarting."
        )

    detail_items = await db_connection.exec(select(models.DetailItem))
    if detail_items:
        return

    await db_connection.insert(
        [models.DetailItem(description=DEFAULT_DETAIL_DESCRIPTION)]
    )
