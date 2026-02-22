from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app import schemas
from app.repositories.model_repo import model_repo

router = APIRouter(prefix="/models", tags=["models"])

@router.post("/", response_model=schemas.ModelRead)
async def create_model(model: schemas.ModelCreate, db: AsyncSession = Depends(get_db)):
    return await model_repo.create(db, model)

@router.get("/", response_model=list[schemas.ModelRead])
async def read_models(db:AsyncSession = Depends(get_db)):
    return await model_repo.get_all(db)

@router.delete("/{model_id}")
async def delete_model(model_id: str, db: AsyncSession = Depends(get_db)):
    result = await model_repo.delete(db, model_id)
    if result == 0:
        raise HTTPException(status_code=404, detail="No models found for this project")
    return {"detail": "Model deleted"}

@router.delete("/project/{project_name}")
async def delete_models_by_project(project_name: str, db: AsyncSession = Depends(get_db)):
    result = await model_repo.delete_by_project(db, project_name)
    
    if result == 0:
        raise HTTPException(status_code=404, detail="No models found for this project")
    
    return {"detail": f"Deleted {result} models for project '{project_name}'"}