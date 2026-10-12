import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer, Float, JSON, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.database import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    manager_id = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)

    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    department = Column(String(100), nullable=False)
    role = Column(String(100), nullable=False)  # e.g. "Backend Engineer"
    seniority = Column(String(50), default="mid")  # junior, mid, senior, lead, principal
    experience_years = Column(Float, default=0)

    tech_stack = Column(JSON, default=list)  # ["Python", "FastAPI", "PostgreSQL"]
    current_workload_percentage = Column(Float, default=0.0)  # 0-100
    weekly_capacity_hours = Column(Float, default=40.0)
    availability_status = Column(String(50), default="available")  # available, busy, on_leave, unavailable
    performance_score = Column(Float, default=75.0)  # 0-100
    salary_band = Column(String(50), nullable=True)  # junior, mid, senior, staff, principal
    timezone = Column(String(100), default="UTC")
    location = Column(String(255), nullable=True)

    avatar_url = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)
    github_url = Column(String(255), nullable=True)
    linkedin_url = Column(String(255), nullable=True)

    # AI fields
    ai_skill_embedding = Column(JSON, nullable=True)  # Vector stored as JSON list
    ai_compatibility_score = Column(Float, default=0.0)

    is_active = Column(Boolean, default=True)
    hire_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship("Organization", back_populates="employees")
    user = relationship("User", back_populates="employee")
    manager = relationship("Employee", remote_side=[id], foreign_keys=[manager_id])
    skills = relationship("EmployeeSkill", back_populates="employee", cascade="all, delete-orphan")
    assigned_tasks = relationship("Task", back_populates="assigned_employee", foreign_keys="Task.assigned_employee_id")


class EmployeeSkill(Base):
    __tablename__ = "employee_skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    skill_name = Column(String(100), nullable=False)
    category = Column(String(100), nullable=True)  # "Programming Language", "Framework", "Tool", "Soft Skill"
    proficiency = Column(Integer, default=3)  # 1-5
    years_experience = Column(Float, default=0)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="skills")
