from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.models.database import get_db
from app.models.user import User
from app.models.employee import Employee
from app.models.project import Project
from app.models.task import Task
from app.models.ai_model import AIRecommendation
from app.core.security import get_current_user

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/dashboard")
async def dashboard_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org_id = current_user.organization_id

    employees = db.query(Employee).filter(
        Employee.organization_id == org_id, Employee.is_active == True
    ).all()
    projects = db.query(Project).filter(Project.organization_id == org_id).all()
    tasks = db.query(Task).join(Project).filter(Project.organization_id == org_id).all()

    # Employee metrics
    total_employees = len(employees)
    avg_workload = sum(e.current_workload_percentage or 0 for e in employees) / max(total_employees, 1)
    overloaded = sum(1 for e in employees if (e.current_workload_percentage or 0) > 85)

    # Project metrics
    active_projects = sum(1 for p in projects if p.status == "active")
    completed_projects = sum(1 for p in projects if p.status == "completed")
    at_risk_projects = sum(1 for p in projects if (p.ai_risk_score or 0) > 50)

    # Task metrics
    total_tasks = len(tasks)
    done_tasks = sum(1 for t in tasks if t.status == "done")
    in_progress = sum(1 for t in tasks if t.status == "in_progress")
    blocked_tasks = sum(1 for t in tasks if t.is_blocked)

    # Burndown data (last 14 days)
    burndown = []
    for i in range(14, -1, -1):
        day = datetime.utcnow() - timedelta(days=i)
        completed_by_day = sum(
            1 for t in tasks
            if t.completed_at and t.completed_at.date() <= day.date()
        )
        burndown.append({"date": day.strftime("%m/%d"), "completed": completed_by_day, "remaining": total_tasks - completed_by_day})

    # Velocity (tasks per week last 4 weeks)
    velocity = []
    for i in range(4, 0, -1):
        week_start = datetime.utcnow() - timedelta(weeks=i)
        week_end = week_start + timedelta(weeks=1)
        week_done = sum(
            1 for t in tasks
            if t.completed_at and week_start <= t.completed_at < week_end
        )
        velocity.append({"week": f"W-{i}", "tasks_completed": week_done, "story_points": week_done * 3})

    # Department workload
    dept_workload = {}
    for e in employees:
        dept = e.department
        if dept not in dept_workload:
            dept_workload[dept] = {"total": 0, "count": 0}
        dept_workload[dept]["total"] += e.current_workload_percentage or 0
        dept_workload[dept]["count"] += 1

    dept_data = [
        {"department": dept, "avg_workload": round(v["total"] / v["count"], 1)}
        for dept, v in dept_workload.items()
    ]

    return {
        "summary": {
            "total_employees": total_employees,
            "avg_workload_pct": round(avg_workload, 1),
            "overloaded_employees": overloaded,
            "active_projects": active_projects,
            "completed_projects": completed_projects,
            "at_risk_projects": at_risk_projects,
            "total_tasks": total_tasks,
            "done_tasks": done_tasks,
            "in_progress_tasks": in_progress,
            "blocked_tasks": blocked_tasks,
            "overall_completion_pct": round(done_tasks / max(total_tasks, 1) * 100, 1),
        },
        "burndown_chart": burndown,
        "velocity_chart": velocity,
        "department_workload": dept_data,
        "project_status_distribution": {
            "planning": sum(1 for p in projects if p.status == "planning"),
            "active": active_projects,
            "paused": sum(1 for p in projects if p.status == "paused"),
            "completed": completed_projects,
            "cancelled": sum(1 for p in projects if p.status == "cancelled"),
        },
    }


@router.get("/workload")
async def workload_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    employees = db.query(Employee).filter(
        Employee.organization_id == current_user.organization_id,
        Employee.is_active == True,
    ).all()

    return {
        "employees": [
            {
                "id": str(e.id),
                "name": e.full_name,
                "department": e.department,
                "role": e.role,
                "workload_pct": e.current_workload_percentage or 0,
                "capacity_hours": e.weekly_capacity_hours or 40,
                "availability": e.availability_status,
                "performance": e.performance_score or 0,
            }
            for e in employees
        ],
        "total": len(employees),
    }
