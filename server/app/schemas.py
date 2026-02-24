# app/schemas.py
# Schemi Pydantic per validazione e serializzazione

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Literal, List
from app.enums.enums import SplitEnum, StatusEnum, MetricEnum

#############################################################
##                   SCHEMI PER MODELS                     ##
#############################################################
class ModelCreate(BaseModel):
    name: str
    project_name: str

class ModelRead(BaseModel):
    id : UUID
    name: str
    project_name: str

    class Config:
        from_attributes = True

##############################################################
##                   SCHEMI PER TRAINING RUNS              ##
##############################################################

class RunCreate(BaseModel):
    model_id: UUID
    status : str = StatusEnum.running
    hyperparameters: Optional[Dict] = None
    note: Optional[str] = None

class RunStatusUpdate(BaseModel):
    run_id : UUID
    new_status : StatusEnum

class RunNotesUpdate(BaseModel):
    run_id: UUID
    new_note : str = None

class RunRead(BaseModel):
    id: UUID
    model_id: UUID
    status: StatusEnum
    started_at: datetime
    finished_at: Optional[datetime]
    hyperparameters: Optional[Dict] = None
    note: Optional[str] = None

    class Config:
        from_attributes = True

##############################################################
##                   SCHEMI PER LOSSES                     ##
##############################################################

class LossCreate(BaseModel):
    run_id : UUID
    step: int
    split: SplitEnum
    value: float

class LossBatchCreate(BaseModel):
    run_id : UUID    
    losses: List[LossCreate]

class LossRead(BaseModel):
    run_id: UUID
    step: int
    split: SplitEnum
    timestamp: datetime
    value: float

    class Config:
        from_attributes = True

###############################################################
##                   SCHEMI PER METRICS                     ##
###############################################################

class MetricCreate(BaseModel):
    run_id : UUID
    step: int
    split: SplitEnum
    metric_name: MetricEnum
    value: float

class MetricBatchCreate(BaseModel):
    run_id : UUID    
    metrics: List[MetricCreate]

class MetricRead(BaseModel):
    run_id: UUID
    step: int
    split: SplitEnum
    metric_name: MetricEnum
    timestamp: datetime
    value: float

    class Config:
        from_attributes = True