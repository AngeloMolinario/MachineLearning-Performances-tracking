from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import get_db
from app import models, schemas
from app.repositories.metrics_repo import metric_repo
from typing import List, Optional

router = APIRouter(prefix="/metric", tags=["metric"])

@router.post("/", response_model=schemas.MetricRead)
async def create_metric(metric: schemas.MetricCreate, db: AsyncSession = Depends(get_db)):
    return await metric_repo.create(db, metric)

@router.post("/batch", response_model=list[schemas.MetricRead])
async def create_loss_batch(metrics: schemas.MetricBatchCreate, db: AsyncSession = Depends(get_db)):
    return await metric_repo.create_batch_loss(db, metrics)

@router.get("/", response_model=List[schemas.MetricRead])
async def get_metrics(
        run_id: str,
        split: Optional[str] = None,
        metric_name: Optional[str] = None,
        limit: Optional[int] = None,
        db: AsyncSession = Depends(get_db)):

    return await metric_repo.get_loss_with_param(db, run_id, metric_name, split, limit)