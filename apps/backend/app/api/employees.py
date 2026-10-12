from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from sqlalchemy import or_, and_
import uuid
from app.models.database import get_db
from app.models.user import User
from app.models.employee import Employee, EmployeeSkill
from app.core.security import get_current_user

router = APIRouter(prefix="/api/employees", tags=["Employees"])


class EmployeeCreate(BaseModel):
    full_name: str
    email: EmailStr
    department: str
    role: str
    seniority: str = "mid"
    experience_years: float = 0
    tech_stack: List[str] = []
    weekly_capacity_hours: float = 40
    availability_status: str = "available"
    salary_band: Optional[str] = None
    timezone: str = "UTC"
    location: Optional[str] = None
    bio: Optional[str] = None


class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    seniority: Optional[str] = None
    experience_years: Optional[float] = None
    tech_stack: Optional[List[str]] = None
    current_workload_percentage: Optional[float] = None
    weekly_capacity_hours: Optional[float] = None
    availability_status: Optional[str] = None
    performance_score: Optional[float] = None
    salary_band: Optional[str] = None
    timezone: Optional[str] = None


def employee_to_dict(e: Employee) -> dict:
    return {
        "id": str(e.id),
        "full_name": e.full_name,
        "email": e.email,
        "department": e.department,
        "role": e.role,
        "seniority": e.seniority,
        "experience_years": e.experience_years,
        "tech_stack": e.tech_stack or [],
        "current_workload_percentage": e.current_workload_percentage,
        "weekly_capacity_hours": e.weekly_capacity_hours,
        "availability_status": e.availability_status,
        "performance_score": e.performance_score,
        "salary_band": e.salary_band,
        "timezone": e.timezone,
        "location": e.location,
        "avatar_url": e.avatar_url,
        "bio": e.bio,
        "is_active": e.is_active,
        "hire_date": e.hire_date.isoformat() if e.hire_date else None,
        "manager_id": str(e.manager_id) if e.manager_id else None,
        "skills": [
            {
                "skill_name": s.skill_name,
                "category": s.category,
                "proficiency": s.proficiency,
                "years_experience": s.years_experience,
            }
            for s in (e.skills or [])
        ],
    }


@router.get("")
async def list_employees(
    search: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    availability: Optional[str] = Query(None),
    skill: Optional[str] = Query(None),
    seniority: Optional[str] = Query(None),
    min_performance: Optional[float] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Employee).filter(
        Employee.organization_id == current_user.organization_id,
        Employee.is_active == True,
    )

    if search:
        query = query.filter(
            or_(
                Employee.full_name.ilike(f"%{search}%"),
                Employee.email.ilike(f"%{search}%"),
                Employee.role.ilike(f"%{search}%"),
            )
        )
    if department:
        query = query.filter(Employee.department == department)
    if availability:
        query = query.filter(Employee.availability_status == availability)
    if seniority:
        query = query.filter(Employee.seniority == seniority)
    if min_performance:
        query = query.filter(Employee.performance_score >= min_performance)

    total = query.count()
    employees = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [employee_to_dict(e) for e in employees],
    }


@router.post("", status_code=201)
async def create_employee(
    data: EmployeeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    employee = Employee(
        id=uuid.uuid4(),
        organization_id=current_user.organization_id,
        **data.dict(),
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee_to_dict(employee)


@router.get("/{employee_id}")
async def get_employee(
    employee_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    employee = db.query(Employee).filter(
        Employee.id == employee_id,
        Employee.organization_id == current_user.organization_id,
    ).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee_to_dict(employee)


@router.put("/{employee_id}")
async def update_employee(
    employee_id: str,
    data: EmployeeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    employee = db.query(Employee).filter(
        Employee.id == employee_id,
        Employee.organization_id == current_user.organization_id,
    ).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    for field, value in data.dict(exclude_none=True).items():
        setattr(employee, field, value)

    db.commit()
    db.refresh(employee)
    return employee_to_dict(employee)


@router.delete("/{employee_id}", status_code=204)
async def delete_employee(
    employee_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    employee = db.query(Employee).filter(
        Employee.id == employee_id,
        Employee.organization_id == current_user.organization_id,
    ).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    employee.is_active = False
    db.commit()


@router.get("/stats/overview")
async def employee_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    employees = db.query(Employee).filter(
        Employee.organization_id == current_user.organization_id,
        Employee.is_active == True,
    ).all()

    if not employees:
        return {"total": 0}

    dept_counts = {}
    skill_counts = {}
    for e in employees:
        dept_counts[e.department] = dept_counts.get(e.department, 0) + 1
        for skill in (e.tech_stack or []):
            skill_counts[skill] = skill_counts.get(skill, 0) + 1

    avg_workload = sum(e.current_workload_percentage or 0 for e in employees) / len(employees)
    avg_performance = sum(e.performance_score or 0 for e in employees) / len(employees)

    return {
        "total": len(employees),
        "available": sum(1 for e in employees if e.availability_status == "available"),
        "busy": sum(1 for e in employees if e.availability_status == "busy"),
        "on_leave": sum(1 for e in employees if e.availability_status == "on_leave"),
        "overloaded": sum(1 for e in employees if (e.current_workload_percentage or 0) > 85),
        "avg_workload_pct": round(avg_workload, 1),
        "avg_performance_score": round(avg_performance, 1),
        "departments": dept_counts,
        "top_skills": sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:20],
    }
