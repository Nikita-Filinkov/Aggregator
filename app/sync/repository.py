from datetime import datetime
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.logger import logger
from app.sync.models import SyncMetadata


class SyncMetadataRepository:
    """Репозиторий для работы с таблицей SyncMetadata"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_with_lock(self) -> Optional[SyncMetadata]:
        """Получить запись с блокировкой для обновления"""
        result = await self.session.execute(
            select(SyncMetadata).where(SyncMetadata.id == 1).with_for_update()
        )
        return result.scalar_one_or_none()

    async def acquire_lock(self) -> tuple[bool, Optional[datetime]]:
        """
        Попытка захватить блокировку для синхронизации.
        Возвращает (успех, last_changed_at) или (False, None) если уже выполняется.
        """
        async with self.session.begin():
            meta = await self.get_with_lock()
            if meta and meta.sync_status == "in_progress":
                return False, None

            last_changed_at = None
            if meta and meta.last_changed_at:
                last_changed_at = meta.last_changed_at

            if not meta:
                await self.create(
                    sync_status="in_progress",
                    last_sync_at=datetime.now(),
                )
            else:
                await self.update(
                    sync_status="in_progress",
                    last_sync_at=datetime.now(),
                )

            return True, last_changed_at

    async def release_lock(
        self, success: bool, last_changed_at: Optional[datetime] = None
    ) -> None:
        """Снять блокировку после синхронизации"""
        logger.info(
            "Снятие блокировки",
            extra={
                "success": success,
                "last_changed_at": str(last_changed_at) if last_changed_at else None,
            },
        )
        if success:
            await self.update(
                last_changed_at=last_changed_at,
                sync_status="success",
            )
        else:
            await self.update(sync_status="failed")
        await self.session.commit()
        logger.info("Блокировка успешно снята")

    async def get(self) -> Optional[SyncMetadata]:
        """Не блокирующие получение метаданных"""
        result = await self.session.execute(
            select(SyncMetadata).where(SyncMetadata.id == 1)
        )
        return result.scalar_one_or_none()

    async def update(self, **kwargs) -> None:
        """Обновление метаданных"""
        query = update(SyncMetadata).where(SyncMetadata.id == 1).values(**kwargs)
        await self.session.execute(query)
        await self.session.commit()

    async def create(self, **kwargs) -> SyncMetadata:
        """Первичное создание строки метаданных"""
        meta = SyncMetadata(id=1, **kwargs)
        self.session.add(meta)
        await self.session.commit()
        return meta
