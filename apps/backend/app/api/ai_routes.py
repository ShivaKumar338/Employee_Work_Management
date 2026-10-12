from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.models.database import get_db
from app.models.user import User
from app.models.employee import Employee
from app.models.project import Project
from app.models.task import Task
from app.models.ai_model import AIRecommendation
from app.core.security import get_current_user
from app.ai.team_recommender import recommend_team
from app.ai.prd_generator import generate_prd
from app.ai.risk_analyzer import analyze_project_risk, balance_workload
import uuid

router = APIRouter(prefix="/api/ai", tags=["AI Engine"])


class TeamRecommendRequest(BaseModel):
    project_description: str
    required_roles: List[Dict[str, Any]]
    required_skills: List[str] = []
    project_id: Optional[str] = None


class PRDRequest(BaseModel):
    description: str
    project_id: Optional[str] = None
    additional_context: Optional[Dict] = None


class RiskAnalysisRequest(BaseModel):
    project_id: str


class WorkloadBalanceRequest(BaseModel):
    department: Optional[str] = None


@router.post("/recommend-team")
async def recommend_team_endpoint(
    data: TeamRecommendRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = recommend_team(
        db=db,
        organization_id=str(current_user.organization_id),
        project_description=data.project_description,
        required_roles=data.required_roles,
        required_skills=data.required_skills,
    )

    # Store recommendation
    rec = AIRecommendation(
        id=uuid.uuid4(),
        organization_id=current_user.organization_id,
        project_id=data.project_id,
        recommendation_type="team_recommendation",
        input_data=data.dict(),
        output_data=result,
        confidence_score=result.get("team_confidence", 0),
        model_used="skill_matcher_v1",
        created_by_id=current_user.id,
    )
    db.add(rec)
    db.commit()

    return result


@router.post("/generate-prd")
async def generate_prd_endpoint(
    data: PRDRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    prd = await generate_prd(data.description, data.additional_context)

    # Store in project if provided
    if data.project_id:
        import json
        project = db.query(Project).filter(
            Project.id == data.project_id,
            Project.organization_id == current_user.organization_id,
        ).first()
        if project:
            project.prd_content = json.dumps(prd)
            db.commit()

    # Store recommendation record
    rec = AIRecommendation(
        id=uuid.uuid4(),
        organization_id=current_user.organization_id,
        project_id=data.project_id,
        recommendation_type="prd_generation",
        input_data={"description": data.description},
        output_data=prd,
        confidence_score=85.0,
        model_used="gpt-4o-mini",
        created_by_id=current_user.id,
    )
    db.add(rec)
    db.commit()

    return prd


@router.post("/predict-risk")
async def predict_risk(
    data: RiskAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(
        Project.id == data.project_id,
        Project.organization_id == current_user.organization_id,
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    tasks = db.query(Task).filter(Task.project_id == data.project_id).all()
    task_emp_ids = {str(t.assigned_employee_id) for t in tasks if t.assigned_employee_id}
    team = db.query(Employee).filter(Employee.id.in_(task_emp_ids)).all()

    result = analyze_project_risk(project, tasks, team)

    # Update project risk score
    project.ai_risk_score = result["risk_score"]
    project.ai_insights = result
    db.commit()

    return result


@router.get("/workload-balance")
async def workload_balance(
    department: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Employee).filter(
        Employee.organization_id == current_user.organization_id,
        Employee.is_active == True,
    )
    if department:
        query = query.filter(Employee.department == department)
    employees = query.all()
    return balance_workload(employees)


@router.post("/generate-sprint")
async def generate_sprint(
    project_id: str,
    sprint_goal: str,
    velocity: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate an AI-planned sprint from backlog tasks."""
    tasks = db.query(Task).filter(
        Task.project_id == project_id,
        Task.status == "todo",
        Task.sprint_id == None,
    ).order_by(Task.ai_priority_score.desc()).limit(velocity).all()

    sprint_tasks = []
    total_hours = 0
    for t in tasks:
        total_hours += t.estimated_hours or 4
        sprint_tasks.append({
            "task_id": str(t.id),
            "title": t.title,
            "estimated_hours": t.estimated_hours or 4,
            "priority": t.priority,
        })
        if total_hours >= velocity * 4:  # roughly capacity
            break

    return {
        "sprint_goal": sprint_goal,
        "suggested_tasks": sprint_tasks,
        "total_estimated_hours": total_hours,
        "recommended_duration_weeks": max(2, min(4, total_hours // 40 + 1)),
    }
