# server/app/repositories/model_repo.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select
from app.repositories.base import BaseRepository
from app.models import Model
from app.schemas import ModelCreate
from pydantic import BaseModel

class ModelUpdate(BaseModel):
    pass

class ModelRepository(BaseRepository[Model, ModelCreate, ModelUpdate]):
        
    async def delete_by_project(self, db: AsyncSession, project_name: str) -> int:
        """
        Cancella tutti i modelli associati a un determinato nome progetto.
        Restituisce il numero di righe (modelli) cancellate.
        """
        stmt = delete(self.model).where(self.model.project_name == project_name)
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount
    
    async def get_by_project_name(self, db: AsyncSession, project_name: str):
        """
        Cerca tutti i modelli con nome project name
        """
        stmt = select(self.model).where(self.model.project_name == project_name)
        result = await db.execute(stmt)
        return list(result.scalars().all())

# Inizializziamo il singleton del repository
model_repo = ModelRepository(Model)