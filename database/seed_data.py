"""
OrchestAI — Database Seed Script
=================================
Populates the local PostgreSQL database with realistic demo data
so you can immediately explore the platform on localhost.

Usage (from project root):
    cd database
    python seed_data.py

Or with a custom DATABASE_URL:
    DATABASE_URL=postgresql://user:pass@localhost:5432/mydb python seed_data.py
"""

import os
import sys
import uuid
from datetime import datetime, timedelta, date
from pathlib import Path

# ---------------------------------------------------------------------------
# Allow running from any directory
# ---------------------------------------------------------------------------
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "apps" / "backend"))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

# ---------------------------------------------------------------------------
# DB connection
# ---------------------------------------------------------------------------
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/orchestai_db"
)

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# ---------------------------------------------------------------------------
# Import models (triggers table creation via Base metadata)
# ---------------------------------------------------------------------------
from app.models.database import Base
from app.models.user import Organization, User
from app.models.employee import Employee, EmployeeSkill
from app.models.project import Project, Sprint
from app.models.task import Task, TaskDependency
from app.models.ai_model import AIRecommendation
from app.models.analytics import AnalyticsSnapshot, ActivityLog
from app.core.security import get_password_hash

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def uid():
    return uuid.uuid4()

NOW = datetime.utcnow()

print("🌱  Starting OrchestAI seed…")

# ---------------------------------------------------------------------------
# 1. Clean existing data (order matters due to FKs)
# ---------------------------------------------------------------------------
print("   Cleaning existing data…")
for model in [
    ActivityLog, AnalyticsSnapshot, AIRecommendation,
    TaskDependency, Task, Sprint, Project,
    EmployeeSkill, Employee, User, Organization
]:
    db.query(model).delete()
db.commit()

# ---------------------------------------------------------------------------
# 2. Organization
# ---------------------------------------------------------------------------
org = Organization(
    id=uid(),
    name="TechForge Inc.",
    slug="techforge",
    domain="techforge.io",
    plan="pro",
    max_employees=200,
    is_active=True,
)
db.add(org)
db.flush()

# ---------------------------------------------------------------------------
# 3. Users (admin + manager + 3 team leads)
# ---------------------------------------------------------------------------
def make_user(email, name, role, password="Demo1234!"):
    return User(
        id=uid(),
        organization_id=org.id,
        email=email,
        hashed_password=get_password_hash(password),
        full_name=name,
        role=role,
        is_active=True,
        is_verified=True,
    )

admin   = make_user("admin@techforge.io",   "Alex Johnson",   "admin")
manager = make_user("manager@techforge.io", "Sarah Chen",     "manager")
lead1   = make_user("alice@techforge.io",   "Alice Martinez", "team_lead")
lead2   = make_user("bob@techforge.io",     "Bob Kumar",      "team_lead")
lead3   = make_user("carol@techforge.io",   "Carol Zhang",    "team_lead")

users = [admin, manager, lead1, lead2, lead3]
db.add_all(users)
db.flush()
print(f"   ✓  Created {len(users)} users  (admin@techforge.io / Demo1234!)")

# ---------------------------------------------------------------------------
# 4. Employees
# ---------------------------------------------------------------------------
emp_data = [
    # (full_name,            email,                      dept,          role,                   seniority, exp, stack,                                     avail,       perf)
    ("Alice Martinez",   "alice@techforge.io",       "Engineering", "Tech Lead",            "lead",    8,  ["Python","FastAPI","PostgreSQL","Redis"],    "available", 92),
    ("Bob Kumar",        "bob@techforge.io",          "Engineering", "Senior Backend Dev",   "senior",  6,  ["Node.js","Go","MongoDB","Kafka"],           "available", 88),
    ("Carol Zhang",      "carol@techforge.io",        "Engineering", "Frontend Engineer",    "senior",  5,  ["React","Next.js","TypeScript","TailwindCSS"],"available",85),
    ("David Osei",       "david@techforge.io",        "Engineering", "Full Stack Developer", "mid",     3,  ["Python","React","PostgreSQL"],              "available", 78),
    ("Emma Wilson",      "emma@techforge.io",         "Engineering", "Backend Developer",    "mid",     4,  ["Java","Spring Boot","MySQL"],               "busy",      80),
    ("Frank Lee",        "frank@techforge.io",        "Data",        "ML Engineer",          "senior",  7,  ["Python","TensorFlow","PyTorch","SQL"],      "available", 90),
    ("Grace Patel",      "grace@techforge.io",        "Design",      "UI/UX Designer",       "senior",  6,  ["Figma","Adobe XD","CSS","React"],           "available", 87),
    ("Henry Brown",      "henry@techforge.io",        "QA",          "QA Engineer",          "mid",     4,  ["Selenium","Pytest","Cypress","Postman"],    "available", 76),
    ("Iris Nguyen",      "iris@techforge.io",         "DevOps",      "DevOps Engineer",      "senior",  5,  ["Docker","Kubernetes","AWS","Terraform"],    "on_leave",  82),
    ("James Thompson",   "james@techforge.io",        "Engineering", "Junior Developer",     "junior",  1,  ["Python","React","Git"],                    "available", 68),
]

employees = []
for (fname, email, dept, role, sen, exp, stack, avail, perf) in emp_data:
    e = Employee(
        id=uid(),
        organization_id=org.id,
        full_name=fname,
        email=email,
        department=dept,
        role=role,
        seniority=sen,
        experience_years=exp,
        tech_stack=stack,
        current_workload_percentage=round(40 + (hash(fname) % 40), 1),
        weekly_capacity_hours=40.0,
        availability_status=avail,
        performance_score=float(perf),
        timezone="UTC",
        is_active=True,
        hire_date=NOW - timedelta(days=exp * 365),
    )
    db.add(e)
    employees.append(e)

db.flush()

# Skills
skill_map = {
    "Python": "Programming Language", "FastAPI": "Framework", "PostgreSQL": "Database",
    "Redis": "Tool", "Node.js": "Runtime", "Go": "Programming Language",
    "MongoDB": "Database", "Kafka": "Tool", "React": "Framework",
    "Next.js": "Framework", "TypeScript": "Programming Language",
    "TailwindCSS": "Framework", "Java": "Programming Language",
    "Spring Boot": "Framework", "MySQL": "Database",
    "TensorFlow": "ML Framework", "PyTorch": "ML Framework", "SQL": "Database",
    "Figma": "Design Tool", "Adobe XD": "Design Tool", "CSS": "Language",
    "Selenium": "Testing", "Pytest": "Testing", "Cypress": "Testing",
    "Postman": "Testing", "Docker": "DevOps", "Kubernetes": "DevOps",
    "AWS": "Cloud", "Terraform": "DevOps", "Git": "Tool",
}

for emp in employees:
    for i, skill in enumerate(emp.tech_stack):
        db.add(EmployeeSkill(
            id=uid(),
            employee_id=emp.id,
            skill_name=skill,
            category=skill_map.get(skill, "Other"),
            proficiency=5 if i == 0 else (4 if i == 1 else 3),
            years_experience=emp.experience_years * (0.9 - i * 0.1),
            is_primary=(i == 0),
        ))

db.flush()
print(f"   ✓  Created {len(employees)} employees with skills")

# ---------------------------------------------------------------------------
# 5. Projects
# ---------------------------------------------------------------------------
proj1 = Project(
    id=uid(), organization_id=org.id, created_by_id=admin.id,
    name="AI Workforce Orchestration Platform",
    description="Build an AI-powered platform to manage workforce, projects, and tasks intelligently.",
    status="active", priority="critical", complexity="enterprise", category="saas_platform",
    start_date=date.today() - timedelta(days=30),
    end_date=date.today() + timedelta(days=90),
    estimated_hours=1200, actual_hours=420,
    completion_percentage=35.0, budget=150000, spent_budget=52000,
    ai_risk_score=28.0, ai_complexity_score=85.0, ai_recommended_team_size=8,
    tech_stack=["Python", "FastAPI", "Next.js", "PostgreSQL", "Redis"],
    tags=["AI", "SaaS", "MVP", "Hackathon"],
)
proj2 = Project(
    id=uid(), organization_id=org.id, created_by_id=manager.id,
    name="Customer Data Analytics Dashboard",
    description="Real-time analytics dashboard with ML-powered insights and predictive reporting.",
    status="active", priority="high", complexity="complex", category="analytics",
    start_date=date.today() - timedelta(days=15),
    end_date=date.today() + timedelta(days=60),
    estimated_hours=600, actual_hours=180,
    completion_percentage=30.0, budget=80000, spent_budget=24000,
    ai_risk_score=18.0, ai_complexity_score=65.0, ai_recommended_team_size=5,
    tech_stack=["Python", "React", "PostgreSQL", "TensorFlow"],
    tags=["Analytics", "ML", "Dashboard"],
)
proj3 = Project(
    id=uid(), organization_id=org.id, created_by_id=manager.id,
    name="Mobile POS System",
    description="Cross-platform point-of-sale system with inventory tracking and payment processing.",
    status="planning", priority="medium", complexity="medium", category="mobile",
    start_date=date.today() + timedelta(days=7),
    end_date=date.today() + timedelta(days=120),
    estimated_hours=800, actual_hours=0,
    completion_percentage=0.0, budget=100000, spent_budget=0,
    ai_risk_score=35.0, ai_complexity_score=55.0, ai_recommended_team_size=6,
    tech_stack=["React Native", "Node.js", "PostgreSQL"],
    tags=["Mobile", "POS", "Retail"],
)

projects = [proj1, proj2, proj3]
db.add_all(projects)
db.flush()
print(f"   ✓  Created {len(projects)} projects")

# ---------------------------------------------------------------------------
# 6. Sprints
# ---------------------------------------------------------------------------
sprint1 = Sprint(
    id=uid(), project_id=proj1.id, name="Sprint 1 — Auth & Core API",
    sprint_number=1, status="completed",
    start_date=date.today() - timedelta(days=28),
    end_date=date.today() - timedelta(days=14),
    velocity=42.0, capacity_hours=160,
)
sprint2 = Sprint(
    id=uid(), project_id=proj1.id, name="Sprint 2 — Dashboard & Employees",
    sprint_number=2, status="active",
    start_date=date.today() - timedelta(days=14),
    end_date=date.today(),
    velocity=0.0, capacity_hours=160,
)
sprint3 = Sprint(
    id=uid(), project_id=proj2.id, name="Sprint 1 — Data Pipeline",
    sprint_number=1, status="active",
    start_date=date.today() - timedelta(days=10),
    end_date=date.today() + timedelta(days=4),
    velocity=0.0, capacity_hours=120,
)

sprints = [sprint1, sprint2, sprint3]
db.add_all(sprints)
db.flush()
print(f"   ✓  Created {len(sprints)} sprints")

# ---------------------------------------------------------------------------
# 7. Tasks (DAG for proj1)
# ---------------------------------------------------------------------------
def make_task(pid, sid, title, desc, ttype, status, priority, emp, sp, est, actual, pct, x, y, cp=False):
    return Task(
        id=uid(), project_id=pid, sprint_id=sid,
        assigned_employee_id=emp.id if emp else None,
        title=title, description=desc,
        task_type=ttype, status=status, priority=priority,
        story_points=sp, estimated_hours=est, actual_hours=actual,
        completion_percentage=pct,
        dag_position_x=x, dag_position_y=y,
        is_critical_path=cp,
        created_at=NOW,
    )

# Project 1 — Sprint 1 tasks (completed)
t1  = make_task(proj1.id, sprint1.id, "Setup FastAPI project structure",    "Init FastAPI with folder layout and config",    "task", "done",        "high",     employees[0], 5,  8,   8,   100, 100, 50,  True)
t2  = make_task(proj1.id, sprint1.id, "Design PostgreSQL schema",           "ERD design and SQL migration scripts",          "task", "done",        "high",     employees[1], 8,  16,  14,  100, 300, 50,  True)
t3  = make_task(proj1.id, sprint1.id, "JWT Authentication system",          "Implement login, refresh token, and guards",    "task", "done",        "critical", employees[0], 13, 24,  22,  100, 500, 50,  True)
t4  = make_task(proj1.id, sprint1.id, "Employee CRUD API",                  "REST endpoints for employee management",        "task", "done",        "high",     employees[1], 8,  16,  15,  100, 700, 50,  False)

# Project 1 — Sprint 2 tasks (in-progress)
t5  = make_task(proj1.id, sprint2.id, "Next.js dashboard layout",           "Sidebar, topbar, dark mode, routing",           "task", "in_progress", "high",     employees[2], 8,  16,  10,  60,  200, 200, True)
t6  = make_task(proj1.id, sprint2.id, "React Flow DAG visualization",       "DAG renderer with zoom, drag and dependency edges","story","in_progress","critical", employees[2], 13, 24,  8,   35,  500, 200, True)
t7  = make_task(proj1.id, sprint2.id, "AI team recommendation engine",      "Skill-match scoring and team builder AI",       "story","todo",        "critical", employees[5], 13, 20,  0,   0,   800, 200, True)
t8  = make_task(proj1.id, sprint2.id, "Analytics charts integration",       "Recharts-based KPI cards and graphs",           "task", "todo",        "medium",   employees[3], 5,  12,  0,   0,   200, 350, False)
t9  = make_task(proj1.id, sprint2.id, "WebSocket real-time updates",        "Live task status broadcast via WS",             "task", "todo",        "high",     employees[1], 8,  16,  0,   0,   500, 350, False)
t10 = make_task(proj1.id, sprint2.id, "Write unit & integration tests",     "Pytest coverage for all API routes",            "task", "todo",        "medium",   employees[7], 5,  12,  0,   0,   800, 350, False)

# Project 2 tasks
t11 = make_task(proj2.id, sprint3.id, "ETL pipeline design",                "Design data ingestion and transformation layer","task", "in_progress", "high",     employees[5], 8,  16,  12,  75,  100, 100, True)
t12 = make_task(proj2.id, sprint3.id, "ML model training pipeline",         "Scikit-learn + TF pipeline for predictions",   "story","todo",        "high",     employees[5], 13, 24,  0,   0,   400, 100, True)
t13 = make_task(proj2.id, sprint3.id, "Dashboard UI components",            "Recharts-based analytics widgets",              "task", "todo",        "medium",   employees[2], 5,  10,  0,   0,   700, 100, False)
t14 = make_task(proj2.id, sprint3.id, "Bug: Data export CSV broken",        "Fix export endpoint returning wrong encoding",  "bug",  "in_progress", "critical", employees[3], 2,  4,   2,   50,  100, 250, False)

all_tasks = [t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11, t12, t13, t14]
db.add_all(all_tasks)
db.flush()
print(f"   ✓  Created {len(all_tasks)} tasks")

# ---------------------------------------------------------------------------
# 8. Task Dependencies (DAG edges)
# ---------------------------------------------------------------------------
deps = [
    (t3, t1),   # JWT depends on project structure
    (t3, t2),   # JWT depends on schema
    (t4, t2),   # Employee CRUD depends on schema
    (t5, t3),   # Dashboard depends on auth
    (t6, t5),   # DAG depends on dashboard
    (t7, t4),   # AI engine depends on employee CRUD
    (t7, t5),   # AI engine depends on dashboard
    (t8, t5),   # Analytics depends on dashboard
    (t9, t3),   # WS depends on auth
    (t10, t4),  # Tests depend on employee CRUD
    (t12, t11), # ML depends on ETL
    (t13, t11), # UI depends on ETL
]
for (task, dep) in deps:
    db.add(TaskDependency(id=uid(), task_id=task.id, depends_on_id=dep.id))

db.flush()
print(f"   ✓  Created {len(deps)} task dependencies (DAG edges)")

# ---------------------------------------------------------------------------
# 9. AI Recommendations
# ---------------------------------------------------------------------------
ai_rec = AIRecommendation(
    id=uid(),
    organization_id=org.id,
    project_id=proj1.id,
    recommendation_type="team_recommendation",
    input_data={"project_id": str(proj1.id), "required_skills": ["Python","FastAPI","React","PostgreSQL"]},
    output_data={
        "recommended_team": [
            {"employee_id": str(employees[0].id), "name": employees[0].full_name, "match_score": 0.97},
            {"employee_id": str(employees[1].id), "name": employees[1].full_name, "match_score": 0.91},
            {"employee_id": str(employees[2].id), "name": employees[2].full_name, "match_score": 0.88},
            {"employee_id": str(employees[5].id), "name": employees[5].full_name, "match_score": 0.85},
        ],
        "reasoning": "Top-scored team by skill overlap and availability for AI orchestration project.",
    },
    confidence_score=0.93,
    model_used="gpt-4o-mini",
    tokens_used=1840,
    created_by_id=admin.id,
)
db.add(ai_rec)

# ---------------------------------------------------------------------------
# 10. Analytics Snapshots
# ---------------------------------------------------------------------------
for i in range(7):
    day = NOW - timedelta(days=6 - i)
    db.add(AnalyticsSnapshot(
        id=uid(),
        organization_id=org.id,
        snapshot_date=day,
        snapshot_type="daily",
        metrics={
            "total_employees": len(employees),
            "active_projects": 2,
            "tasks_completed": 4 + i * 2,
            "tasks_in_progress": 3,
            "avg_workload": round(62 + i * 1.5, 1),
            "velocity": round(8 + i * 0.8, 1),
            "ai_recommendations_generated": i + 1,
            "budget_utilization": round(34 + i * 1.2, 1),
        },
    ))

# ---------------------------------------------------------------------------
# 11. Activity Logs
# ---------------------------------------------------------------------------
log_actions = [
    (admin,   "user.login",        "user",    str(admin.id)),
    (admin,   "project.created",   "project", str(proj1.id)),
    (manager, "employee.created",  "employee",str(employees[0].id)),
    (lead1,   "task.status_update","task",    str(t3.id)),
    (lead2,   "ai.recommendation", "project", str(proj1.id)),
]
for (u, action, rtype, rid) in log_actions:
    db.add(ActivityLog(
        id=uid(), organization_id=org.id, user_id=u.id,
        action=action, resource_type=rtype, resource_id=rid,
        ip_address="127.0.0.1",
    ))

# ---------------------------------------------------------------------------
# Commit everything
# ---------------------------------------------------------------------------
db.commit()
db.close()

print("")
print("✅  Seed complete!")
print("")
print("   Login credentials:")
print("   ─────────────────────────────────────────")
print("   Admin:   admin@techforge.io   / Demo1234!")
print("   Manager: manager@techforge.io / Demo1234!")
print("   Lead:    alice@techforge.io   / Demo1234!")
print("   ─────────────────────────────────────────")
print("")
print("   API docs → http://localhost:8000/api/docs")
print("   Frontend → http://localhost:3000")
