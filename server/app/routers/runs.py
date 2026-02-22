from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update

from app.db import get_db
from app import models, schemas
from app.repositories.run_repo import run_repo
from app.repositories.model_repo import model_repo

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("/", response_model=schemas.RunRead)
async def create_run(run: schemas.RunCreate, db: AsyncSession = Depends(get_db)):
    return await run_repo.create(db, run)


@router.get("/runbymodels/{model_id}", response_model=list[schemas.RunRead])
async def read_runs(model_id: str, db: AsyncSession = Depends(get_db)):
    result = await run_repo.get_by_model_id(db, model_id)
    if not result:
        raise HTTPException(status_code=404, detail="Run not found")
    return result

@router.get("/runbyproject/{project_name}", response_model=list[schemas.RunRead])
async def read_runs_by_project(project_name: str, db: AsyncSession = Depends(get_db)):
    project_exists = await model_repo.get_by_project_name(db, project_name)
    if not project_exists:
        raise HTTPException(status_code=404, detail="Project name not found")

    return await run_repo.get_by_project_name(db, project_name)


@router.delete("/{run_id}")
async def delete_run(run_id: str, db: AsyncSession = Depends(get_db)):
    result = await run_repo.batch_delete(db, run_id)
    return {"detail": "Run deleted", "Affected row" : result}

@router.patch("/update_status")
async def update_status(payload: schemas.RunStatusUpdate, db: AsyncSession = Depends(get_db)):
    # Richiami semplicemente il tuo metodo custom!
    rows_updated = await run_repo.update_status(db, new_update=payload)
    
    # Restituisci il numero di righe modificate
    return {"rows_updated": rows_updated}