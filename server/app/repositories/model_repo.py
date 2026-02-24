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
    
    async def get_by_model_name(self, db:AsyncSession, model_name:str):
        """
            Cerca tutti i modelli con un model name
        """
        stmt = select(self.model).where(self.model.name == model_name)
        results = await db.execute(stmt)
        return list(results.scalars().all())

    async def get_by_project_name(self, db: AsyncSession, project_name: str):
        """
        Cerca tutti i modelli con nome project name
        """
        stmt = select(self.model).where(self.model.project_name == project_name)
        result = await db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_by_name_and_project_name(self, db:AsyncSession, model_name:str, project_name:str):
        """
            Restituisce il model_id associato alla coppia univoca (model_name, project_name)
        """
        stmt = select(self.model).where(self.model.project_name == project_name).where(self.model.name == model_name)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
        

# Inizializziamo il singleton del repository
model_repo = ModelRepository(Model)