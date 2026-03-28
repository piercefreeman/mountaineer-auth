import pytest
import pytest_asyncio
from example_app import models
from example_app.bootstrap import bootstrap_database
from example_app.constants import DEFAULT_DETAIL_DESCRIPTION
from example_app.controllers.detail import DetailController
from example_app.controllers.home import HomeController
from iceaxe import DBConnection, select


@pytest_asyncio.fixture
async def user_record(db_connection: DBConnection) -> models.User:
    user = models.User(
        email="person@example.com",
        hashed_password=models.User.get_password_hash("password123"),
    )
    await db_connection.insert([user])
    return user


@pytest.mark.asyncio
async def test_bootstrap_database_is_idempotent(db_connection: DBConnection):
    await bootstrap_database(db_connection)
    await bootstrap_database(db_connection)

    detail_items = await db_connection.exec(select(models.DetailItem))

    assert len(detail_items) == 1
    assert detail_items[0].description == DEFAULT_DETAIL_DESCRIPTION


@pytest.mark.asyncio
async def test_home_render_exposes_auth_state(
    db_connection: DBConnection,
    user_record: models.User,
):
    await bootstrap_database(db_connection)
    controller = HomeController()

    render = await controller.render(session=db_connection, user=user_record)

    assert render.is_authenticated is True
    assert render.user_email == user_record.email
    assert render.detail_id is not None


@pytest.mark.asyncio
async def test_detail_render_includes_authenticated_user(
    db_connection: DBConnection,
    user_record: models.User,
):
    await bootstrap_database(db_connection)
    detail_items = await db_connection.exec(select(models.DetailItem))
    detail_item = detail_items[0]

    controller = DetailController()
    render = await controller.render(
        detail_id=detail_item.id,
        user=user_record,
        session=db_connection,
    )

    assert render.id == detail_item.id
    assert render.description == DEFAULT_DETAIL_DESCRIPTION
    assert render.user_email == user_record.email
    assert render.user_id == str(user_record.id)
