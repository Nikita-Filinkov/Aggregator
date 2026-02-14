from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.sync.models import SyncMetadata


class SyncMetadataRepository:
    """Репозиторий для работы с таблицей SyncMetadata"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self) -> Optional[SyncMetadata]:
        result = await self.session.execute(
            select(SyncMetadata).where(SyncMetadata.id == 1)
        )
        return result.scalar_one_or_none()

    async def update(self, **kwargs) -> None:
        query = update(SyncMetadata).where(SyncMetadata.id == 1).values(**kwargs)
        await self.session.execute(query)
        await self.session.commit()

    async def create(self, **kwargs) -> SyncMetadata:
        meta = SyncMetadata(id=1, **kwargs)
        self.session.add(meta)
        await self.session.commit()
        return meta
