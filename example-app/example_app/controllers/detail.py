from fastapi import Depends
from iceaxe import DBConnection
from iceaxe.mountaineer import DatabaseDependencies
from pydantic import BaseModel

from mountaineer import APIException, ControllerBase, Metadata, RenderBase, sideeffect

from example_app import models
from mountaineer_auth import AuthDependencies
from mountaineer_auth.models import UserAuthMixin


class NotFoundException(APIException):
    status_code = 404
    detail = "Detail item not found"


class UpdateTextRequest(BaseModel):
    description: str


class DetailRender(RenderBase):
    id: int
    description: str
    is_admin: bool
    is_verified: bool
    user_email: str
    user_id: str


class DetailController(ControllerBase):
    url = "/detail/{detail_id}/"
    view_path = "/app/detail/page.tsx"

    def __init__(self):
        super().__init__()

    async def render(
        self,
        detail_id: int,
        user: UserAuthMixin = Depends(AuthDependencies.require_valid_user),
        session: DBConnection = Depends(DatabaseDependencies.get_db_connection),
    ) -> DetailRender:
        detail_item = await session.get(models.DetailItem, detail_id)
        if not detail_item:
            raise NotFoundException()

        return DetailRender(
            id=detail_item.id,
            description=detail_item.description,
            is_admin=user.is_admin,
            is_verified=user.is_verified,
            metadata=Metadata(title=f"Detail: {detail_id}"),
            user_email=user.email,
            user_id=str(user.id),
        )

    @sideeffect
    async def update_text(
        self,
        detail_id: int,
        payload: UpdateTextRequest,
        _user: UserAuthMixin = Depends(AuthDependencies.require_valid_user),
        session: DBConnection = Depends(DatabaseDependencies.get_db_connection),
    ) -> None:
        detail_item = await session.get(models.DetailItem, detail_id)
        if not detail_item:
            raise NotFoundException()

        detail_item.description = payload.description.strip()
        await session.update([detail_item])
