from fastapi import Depends
from iceaxe import DBConnection, select
from iceaxe.mountaineer import DatabaseDependencies

from mountaineer import ControllerBase, Metadata, RenderBase

from example_app import models
from mountaineer_auth import AuthDependencies
from mountaineer_auth.models import UserAuthMixin


class HomeRender(RenderBase):
    detail_description: str | None
    detail_id: int | None
    is_authenticated: bool
    user_email: str | None


class HomeController(ControllerBase):
    url = "/"
    view_path = "/app/home/page.tsx"

    async def render(
        self,
        session: DBConnection = Depends(DatabaseDependencies.get_db_connection),
        user: UserAuthMixin | None = Depends(AuthDependencies.peek_user),
    ) -> HomeRender:
        detail_items = await session.exec(select(models.DetailItem))
        detail_item = detail_items[0] if detail_items else None

        return HomeRender(
            metadata=Metadata(
                title="Mountaineer Auth Example",
            ),
            detail_description=detail_item.description if detail_item else None,
            detail_id=detail_item.id if detail_item else None,
            is_authenticated=user is not None,
            user_email=user.email if user else None,
        )
