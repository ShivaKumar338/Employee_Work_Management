import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    sprint_id = Column(UUID(as_uuid=True), ForeignKey("sprints.id", ondelete="SET NULL"), nullable=True)
    assigned_employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    parent_task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)

    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    task_type = Column(String(50), default="task")  # task, bug, story, epic, subtask
    status = Column(String(50), default="todo")  # todo, in_progress, review, blocked, done, cancelled
    priority = Column(String(50), default="medium")  # low, medium, high, critical

    # DAG fields
    dag_position_x = Column(Float, default=0.0)
    dag_position_y = Column(Float, default=0.0)
    is_critical_path = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)
    blocking_reason = Column(Text, nullable=True)

    # Estimation
    story_points = Column(Integer, nullable=True)
    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, default=0.0)
    deadline = Column(DateTime, nullable=True)

    # AI fields
    ai_risk_score = Column(Float, default=0.0)  # 0-100
    ai_priority_score = Column(Float, default=0.0)
    ai_complexity = Column(String(50), nullable=True)

    completion_percentage = Column(Float, default=0.0)
    labels = Column(JSON, default=list)

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="tasks")
    sprint = relationship("Sprint", back_populates="tasks")
    assigned_employee = relationship("Employee", back_populates="assigned_tasks", foreign_keys=[assigned_employee_id])
    subtasks = relationship("Task", foreign_keys=[parent_task_id])

    dependencies = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.task_id",
        back_populates="task",
        cascade="all, delete-orphan"
    )
    dependents = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.depends_on_id",
        back_populates="depends_on_task",
    )


class TaskDependency(Base):
    __tablename__ = "task_dependencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    depends_on_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    dependency_type = Column(String(50), default="finish_to_start")  # finish_to_start, start_to_start, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", foreign_keys=[task_id], back_populates="dependencies")
    depends_on_task = relationship("Task", foreign_keys=[depends_on_id], back_populates="dependents")
