import uuid
from sqlalchemy import Column, String, Float, DateTime, Integer, ForeignKey, PrimaryKeyConstraint, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Enum, Index

from app.db import Base
from app.enums.enums import StatusEnum, SplitEnum, MetricEnum


class Model(Base):
    __tablename__ = "models"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    project_name = Column(String, nullable=False)

    runs = relationship("TrainingRun", back_populates="model", cascade="all, delete-orphan")
    __table_args__ = (
        UniqueConstraint("name", "project_name", name="uq_model_name_project"),
    )

class TrainingRun(Base):
    __tablename__ = "training_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id"), nullable=False)

    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)

    status = Column(Enum(StatusEnum), nullable=False, default="running")  
    hyperparameters = Column(JSON)
    note = Column(String, nullable=True)
    

    model = relationship("Model", back_populates="runs")

    losses = relationship("Loss", back_populates="run", cascade="all, delete-orphan")
    metrics = relationship("Metric", back_populates="run", cascade="all, delete-orphan")


class Loss(Base):
    __tablename__ = "losses"

    run_id = Column(UUID(as_uuid=True), ForeignKey("training_runs.id"), nullable=False)
    step = Column(Integer, nullable=False)
    split = Column(Enum(SplitEnum), nullable=False)
    task_name = Column(String, nullable=False, default="__single_task__")

    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    value = Column(Float, nullable=False)

    run = relationship("TrainingRun", back_populates="losses")

    __table_args__ = (
        PrimaryKeyConstraint("run_id", "step", "split", "task_name"),
        Index("idx_loss_run_split_step", "run_id", "split", "step", "task_name"),
    )

class Metric(Base):
    __tablename__ = "metrics"

    run_id = Column(UUID(as_uuid=True), ForeignKey("training_runs.id"), nullable=False)
    step = Column(Integer, nullable=False)
    split = Column(Enum(SplitEnum), nullable=False)
    metric_name = Column(Enum(MetricEnum), nullable=False)

    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    value = Column(Float, nullable=False)

    run = relationship("TrainingRun", back_populates="metrics")

    __table_args__ = (
        PrimaryKeyConstraint("run_id", "step", "split", "metric_name"),
        Index("idx_metric_run_split_step", "run_id", "split", "step"),
    )
