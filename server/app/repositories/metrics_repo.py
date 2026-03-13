# server/app/repositories/loss_repo.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select
from app.repositories.base import BaseRepository
from app.models import Metric
from app.enums.enums import MetricEnum
from app.schemas import MetricCreate, MetricBatchCreate
from pydantic import BaseModel
from typing import Optional

class MetricUpdate(BaseModel):
    pass

class MetricRepository(BaseRepository[Metric, MetricCreate, MetricUpdate]):
    
    async def create_batch_metrics(self, db:AsyncSession, batch:MetricBatchCreate):
        metrics = [Metric(**metric.model_dump()) for metric in batch.metrics]
        db.add_all(metrics)
        await db.commit()
        for metric in metrics:
            await db.refresh(metric)
        return metrics
    
    async def get_metrics_with_param(self, db:AsyncSession, run_id: str, metric_name:Optional[str] = None ,split: Optional[str] = None, limit: Optional[int] = None):
        stmt = select(Metric).where(Metric.run_id == run_id)
        if split:
            stmt = stmt.where(Metric.split == split)
        if limit:
            stmt = stmt.limit(limit)
        if metric_name:
            stmt = stmt.where(Metric.metric_name == metric_name)
        stmt = stmt.order_by(Metric.step.desc())
        result = await db.execute(stmt)
        return result.scalars().all()

metric_repo = MetricRepository(Metric)