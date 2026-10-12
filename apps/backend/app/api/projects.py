from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime
import uuid
from app.models.database import get_db
from app.models.user import User
from app.models.project import Project, Sprint
from app.models.task import Task
from app.models.employee import Employee
from app.core.security import get_current_user

router = APIRouter(prefix="/api/projects", tags=["Projects"])


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    priority: str = "medium"
    category: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    tech_stack: List[str] = []
    tags: List[str] = []
    budget: Optional[float] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    completion_percentage: Optional[float] = None
    end_date: Optional[date] = None


def project_to_dict(p: Project, db: Session) -> dict:
    task_count = db.query(Task).filter(Task.project_id == p.id).count()
    done_count = db.query(Task).filter(Task.project_id == p.id, Task.status == "done").count()
    team_ids = db.query(Task.assigned_employee_id).filter(
        Task.project_id == p.id, Task.assigned_employee_id.isnot(None)
    ).distinct().all()

    return {
        "id": str(p.id),
        "name": p.name,
        "description": p.description,
        "status": p.status,
        "priority": p.priority,
        "complexity": p.complexity,
        "category": p.category,
        "start_date": p.start_date.isoformat() if p.start_date else None,
        "end_date": p.end_date.isoformat() if p.end_date else None,
        "deadline": p.deadline.isoformat() if p.deadline else None,
        "estimated_hours": p.estimated_hours,
        "actual_hours": p.actual_hours,
        "completion_percentage": p.completion_percentage,
        "budget": p.budget,
        "spent_budget": p.spent_budget,
        "ai_risk_score": p.ai_risk_score,
        "ai_recommended_team_size": p.ai_recommended_team_size,
        "tech_stack": p.tech_stack or [],
        "tags": p.tags or [],
        "task_count": task_count,
        "done_task_count": done_count,
        "team_size": len(team_ids),
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


@router.get("")
async def list_projects(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Project).filter(Project.organization_id == current_user.organization_id)

    if status:
        query = query.filter(Project.status == status)
    if priority:
        query = query.filter(Project.priority == priority)
    if search:
        query = query.filter(Project.name.ilike(f"%{search}%"))

    total = query.count()
    projects = query.order_by(Project.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [project_to_dict(p, db) for p in projects],
    }


@router.post("", status_code=201)
async def create_project(
    data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = Project(
        id=uuid.uuid4(),
        organization_id=current_user.organization_id,
        created_by_id=current_user.id,
        **data.dict(),
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project_to_dict(project, db)


@router.get("/stats/overview")
async def project_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    projects = db.query(Project).filter(Project.organization_id == current_user.organization_id).all()
    return {
        "total": len(projects),
        "active": sum(1 for p in projects if p.status == "active"),
        "planning": sum(1 for p in projects if p.status == "planning"),
        "completed": sum(1 for p in projects if p.status == "completed"),
        "at_risk": sum(1 for p in projects if (p.ai_risk_score or 0) > 50),
        "avg_completion": round(sum(p.completion_percentage or 0 for p in projects) / max(len(projects), 1), 1),
    }


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.organization_id == current_user.organization_id,
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project_to_dict(project, db)


@router.put("/{project_id}")
async def update_project(
    project_id: str,
    data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.organization_id == current_user.organization_id,
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    for field, value in data.dict(exclude_none=True).items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project_to_dict(project, db)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.organization_id == current_user.organization_id,
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project.status = "cancelled"
    db.commit()
