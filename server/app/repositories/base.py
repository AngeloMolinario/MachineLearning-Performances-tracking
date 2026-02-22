# server/app/repositories/base.py
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.db import Base 

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, ident: Any) -> Optional[ModelType]:
        """
        Recupera un singolo record tramite la sua Primary Key.
        Accetta un valore singolo (UUID, int) o una tupla per chiavi composite.
        """
        return await db.get(self.model, ident)

    async def get_all(self, db: AsyncSession, limit: int = -1) -> List[ModelType]:
        """
        Recupera una lista di record con supporto base per la paginazione.
        """
        stmt = select(self.model)
        if limit > 0:
            stmt = stmt.limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    
    async def create(self, db: AsyncSession, obj_in: CreateSchemaType) -> ModelType:
        """
        Crea un nuovo record a partire da uno schema Pydantic.
        """
        obj_in_data = obj_in.model_dump()
        db_obj = self.model(**obj_in_data)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, 
        db: AsyncSession, 
        db_obj: ModelType, 
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Aggiorna un record esistente.
        Accetta sia uno schema Pydantic di aggiornamento, sia un normale dizionario.
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
            
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
                
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, ident: Any) -> int:
        """
        Cerca un record tramite Primary Key e lo cancella.
        Restituisce il numero di righe cancellate (1 se cancellato, 0 se non trovato).
        """
        obj = await self.get(db, ident)
        if obj:
            await db.delete(obj)
            await db.commit()
            return 1  # Record trovato e cancellato
            
        return 0  # Nessun record trovato