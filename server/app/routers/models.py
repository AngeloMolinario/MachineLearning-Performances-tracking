from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app import schemas
from app.repositories.model_repo import model_repo

router = APIRouter(prefix="/models", tags=["models"])

@router.post("/", response_model=schemas.ModelRead)
async def create_model(model: schemas.ModelCreate, db: AsyncSession = Depends(get_db)):
    result = await model_repo.create(db, model)
    if result is None:
        raise HTTPException(status_code=409, detail="Record already exists. Model name and project already used")
    return result

@router.get("/", response_model=list[schemas.ModelRead])
async def read_models(db:AsyncSession = Depends(get_db)):
    """
        Return the list of all the registered model
    """
    return await model_repo.get_all(db)

@router.get("/{project_name}/", response_model=schemas.ModelRead)
async def get_by_model_name(model_name: str, project_name: str, db:AsyncSession = Depends(get_db)):
    """
        Return a single model id identified by its name and project.
        (NOTE: Since the couple name and project name is unique in the db it retun a single model id)
    """
    return await model_repo.get_by_name_and_project_name(db, model_name, project_name)


@router.delete("/{model_id}")
async def delete_model(model_id: str, db: AsyncSession = Depends(get_db)):
    """
        Request the delete of a model by its id
    """
    result = await model_repo.delete(db, model_id)
    if result == 0:
        raise HTTPException(status_code=404, detail="No models found for this project")
    return {"detail": "Model deleted"}

@router.delete("/project/{project_name}")
async def delete_models_by_project(project_name: str, db: AsyncSession = Depends(get_db)):
    """
        Delete all the models associated to a project name.
    """
    result = await model_repo.delete_by_project(db, project_name)
    
    if result == 0:
        raise HTTPException(status_code=404, detail="No models found for this project")
    
    return {"detail": f"Deleted {result} models for project '{project_name}'"}