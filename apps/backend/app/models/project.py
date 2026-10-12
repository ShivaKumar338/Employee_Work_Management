import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer, Float, JSON, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="planning")  # planning, active, paused, completed, cancelled
    priority = Column(String(50), default="medium")  # low, medium, high, critical
    complexity = Column(String(50), default="medium")  # simple, medium, complex, enterprise
    category = Column(String(100), nullable=True)  # e.g. "web_app", "ml_platform", "mobile_app"

    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    deadline = Column(DateTime, nullable=True)
    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, default=0.0)

    completion_percentage = Column(Float, default=0.0)
    budget = Column(Float, nullable=True)
    spent_budget = Column(Float, default=0.0)

    # AI fields
    ai_risk_score = Column(Float, default=0.0)  # 0-100
    ai_complexity_score = Column(Float, default=0.0)
    ai_recommended_team_size = Column(Integer, nullable=True)
    ai_insights = Column(JSON, nullable=True)
    prd_content = Column(Text, nullable=True)

    tech_stack = Column(JSON, default=list)
    tags = Column(JSON, default=list)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship("Organization", back_populates="projects")
    sprints = relationship("Sprint", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    ai_recommendations = relationship("AIRecommendation", back_populates="project", cascade="all, delete-orphan")


class Sprint(Base):
    __tablename__ = "sprints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)

    name = Column(String(255), nullable=False)
    goal = Column(Text, nullable=True)
    sprint_number = Column(Integer, default=1)
    status = Column(String(50), default="planning")  # planning, active, completed, cancelled
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    velocity = Column(Float, default=0.0)  # Story points completed
    capacity_hours = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="sprints")
    tasks = relationship("Task", back_populates="sprint")
