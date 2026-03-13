# server/app/repositories/loss_repo.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select
from app.repositories.base import BaseRepository
from app.models import Loss
from app.schemas import LossCreate, LossBatchCreate
from pydantic import BaseModel
from typing import Optional

class LossUpdate(BaseModel):
    pass

class LossRepository(BaseRepository[Loss, LossCreate, LossUpdate]):
    
    async def create_batch_loss(self, db:AsyncSession, batch:LossBatchCreate):
        losses = [Loss(**loss.model_dump()) for loss in batch.losses]
        db.add_all(losses)
        await db.commit()
        for loss in losses:
            await db.refresh(loss)
        return losses
    
    async def get_loss_with_param(self, db:AsyncSession, run_id: str, split: Optional[str] = None, limit: Optional[int] = None):
        stmt = select(Loss).where(Loss.run_id == run_id)
        if split:
            stmt = stmt.where(Loss.split == split)
        if limit:
            stmt = stmt.limit(limit)
        stmt = stmt.order_by(Loss.step.desc())
        result = await db.execute(stmt)
        return result.scalars().all()

loss_repo = LossRepository(Loss)