from iceaxe import DBConnection, select
from iceaxe.schemas.cli import create_all

from example_app import models
from example_app.constants import DEFAULT_DETAIL_DESCRIPTION


async def bootstrap_database(db_connection: DBConnection) -> None:
    await create_all(db_connection=db_connection)

    detail_items = await db_connection.exec(select(models.DetailItem))
    if detail_items:
        return

    await db_connection.insert(
        [models.DetailItem(description=DEFAULT_DETAIL_DESCRIPTION)]
    )
