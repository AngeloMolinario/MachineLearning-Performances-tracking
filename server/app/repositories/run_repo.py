# server/app/repositories/run_repo.py
from app.repositories.base import BaseRepository
from app import models
from app.schemas import RunCreate, RunStatusUpdate
from app.enums.enums import StatusEnum  # Assicurati di importare l'Enum se lo usi!
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from uuid import UUID
from datetime import datetime, timezone

class RunRepository(BaseRepository[models.TrainingRun, RunCreate, RunStatusUpdate]):
    
    async def get_by_model_id(self, db: AsyncSession, model_id: str):
        stmt = select(self.model).where(self.model.model_id == model_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_by_project_name(self, db: AsyncSession, project_name: str):
        stmt = (
            select(models.TrainingRun)
            .join(models.Model, models.TrainingRun.model_id == models.Model.id)
            .where(models.Model.project_name == project_name)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def batch_delete(self, db: AsyncSession, ids: str):
        # 1. Convertiamo in lista di UUID
        uuid_list = [UUID(r.strip()) for r in ids.split(",")]
        
        # 2. Creiamo la query (stmt)
        stmt = delete(models.TrainingRun).where(models.TrainingRun.id.in_(uuid_list))
        
        # 3. Eseguiamo
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount
    
    async def update_status(self, db: AsyncSession, new_update: RunStatusUpdate):
        
        run_id = new_update.run_id          
        new_status = new_update.new_status  
        
        status_value = new_status.value if hasattr(new_status, 'value') else new_status
        
        if status_value == 'completed':
            stmt = (
                update(models.TrainingRun)
                .where(models.TrainingRun.id == run_id)
                # Passa entrambi gli argomenti nello stesso .values()
                .values(
                    status=new_status, 
                    finished_at=datetime.now(timezone.utc)
                )
            )
        else:
            stmt = (
                update(models.TrainingRun)
                .where(models.TrainingRun.id == run_id)
                .values(status=new_status)
            )
            
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount

run_repo = RunRepository(models.TrainingRun)