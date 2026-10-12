from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
from app.models.database import get_db
from app.models.user import User
from app.models.task import Task, TaskDependency
from app.models.project import Project
from app.core.security import get_current_user
from app.ai.dag_engine import DAGEngine

router = APIRouter(prefix="/api", tags=["Tasks & DAG"])


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    task_type: str = "task"
    priority: str = "medium"
    status: str = "todo"
    estimated_hours: Optional[float] = None
    story_points: Optional[int] = None
    assigned_employee_id: Optional[str] = None
    sprint_id: Optional[str] = None
    deadline: Optional[datetime] = None
    labels: List[str] = []
    dag_position_x: float = 0
    dag_position_y: float = 0
    dependencies: List[str] = []  # List of task IDs this depends on


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    assigned_employee_id: Optional[str] = None
    completion_percentage: Optional[float] = None
    dag_position_x: Optional[float] = None
    dag_position_y: Optional[float] = None


def task_to_dict(t: Task) -> dict:
    return {
        "id": str(t.id),
        "project_id": str(t.project_id),
        "sprint_id": str(t.sprint_id) if t.sprint_id else None,
        "title": t.title,
        "description": t.description,
        "task_type": t.task_type,
        "status": t.status,
        "priority": t.priority,
        "estimated_hours": t.estimated_hours,
        "actual_hours": t.actual_hours,
        "story_points": t.story_points,
        "completion_percentage": t.completion_percentage,
        "assigned_employee_id": str(t.assigned_employee_id) if t.assigned_employee_id else None,
        "is_critical_path": t.is_critical_path,
        "is_blocked": t.is_blocked,
        "ai_risk_score": t.ai_risk_score,
        "labels": t.labels or [],
        "dag_position_x": t.dag_position_x,
        "dag_position_y": t.dag_position_y,
        "deadline": t.deadline.isoformat() if t.deadline else None,
        "dependencies": [str(d.depends_on_id) for d in (t.dependencies or [])],
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }


@router.get("/tasks")
async def list_tasks(
    project_id: Optional[str] = Query(None),
    sprint_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Task).join(Project).filter(
        Project.organization_id == current_user.organization_id
    )
    if project_id:
        query = query.filter(Task.project_id == project_id)
    if sprint_id:
        query = query.filter(Task.sprint_id == sprint_id)
    if status:
        query = query.filter(Task.status == status)
    if assigned_to:
        query = query.filter(Task.assigned_employee_id == assigned_to)

    tasks = query.all()
    return {"items": [task_to_dict(t) for t in tasks], "total": len(tasks)}


@router.post("/tasks", status_code=201)
async def create_task(
    project_id: str,
    data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.organization_id == current_user.organization_id,
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    task_data = data.dict(exclude={"dependencies"})
    task = Task(id=uuid.uuid4(), project_id=project_id, created_by_id=current_user.id, **task_data)
    db.add(task)
    db.flush()

    for dep_id in data.dependencies:
        dep = TaskDependency(
            id=uuid.uuid4(),
            task_id=task.id,
            depends_on_id=dep_id,
        )
        db.add(dep)

    db.commit()
    db.refresh(task)
    return task_to_dict(task)


@router.put("/tasks/{task_id}")
async def update_task(
    task_id: str,
    data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = db.query(Task).join(Project).filter(
        Task.id == task_id,
        Project.organization_id == current_user.organization_id,
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    for field, value in data.dict(exclude_none=True).items():
        setattr(task, field, value)

    if data.status == "done" and not task.completed_at:
        task.completed_at = datetime.utcnow()
        task.completion_percentage = 100
    if data.status == "in_progress" and not task.started_at:
        task.started_at = datetime.utcnow()

    db.commit()
    db.refresh(task)
    return task_to_dict(task)


@router.delete("/tasks/{task_id}", status_code=204)
async def delete_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = db.query(Task).join(Project).filter(
        Task.id == task_id,
        Project.organization_id == current_user.organization_id,
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()


@router.get("/dag/{project_id}")
async def get_dag(
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

    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    nodes = [task_to_dict(t) for t in tasks]
    edges = []
    for t in tasks:
        for dep in (t.dependencies or []):
            edges.append({
                "id": f"{dep.depends_on_id}->{t.id}",
                "source": str(dep.depends_on_id),
                "target": str(t.id),
                "type": dep.dependency_type,
            })

    return {"nodes": nodes, "edges": edges, "project": {"id": str(project.id), "name": project.name}}


@router.post("/dag/analyze/{project_id}")
async def analyze_dag(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    node_data = [
        {
            "id": str(t.id),
            "title": t.title,
            "estimated_hours": t.estimated_hours or 0,
            "status": t.status,
            "ai_risk_score": t.ai_risk_score or 0,
            "dependencies": [str(d.depends_on_id) for d in (t.dependencies or [])],
        }
        for t in tasks
    ]

    engine = DAGEngine(node_data)
    analysis = engine.analyze()

    # Update critical path in DB
    if analysis.get("critical_path"):
        for task_id in analysis["critical_path"]["task_ids"]:
            db.query(Task).filter(Task.id == task_id).update({"is_critical_path": True})
        db.commit()

    return analysis


@router.post("/dag/validate")
async def validate_dag(
    nodes: List[dict],
    current_user: User = Depends(get_current_user),
):
    engine = DAGEngine(nodes)
    return engine.validate()
