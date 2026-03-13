from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from uuid import UUID
from app.db import get_db
from app.repositories.loss_repo import loss_repo
from app import models, schemas
from typing import List, Optional

router = APIRouter(prefix="/loss", tags=["loss"])

@router.post("/", response_model=schemas.LossRead)
async def create_loss(loss: schemas.LossCreate, db: AsyncSession = Depends(get_db)):
    return await loss_repo.create(db, loss)

@router.post("/batch", response_model=list[schemas.LossRead])
async def create_loss_batch(loss_batch: schemas.LossBatchCreate, db: AsyncSession = Depends(get_db)):
    return await loss_repo.create_loss_batch(db, loss_batch)

@router.get("/", response_model=List[schemas.LossRead])
async def get_losses(
        run_id: str,
        split: Optional[str] = None,
        task_name: Optional[str] = None,
        limit: Optional[int] = None,
        db: AsyncSession = Depends(get_db)):

    return await loss_repo.get_loss_with_param(db, run_id, task_name, split, limit)