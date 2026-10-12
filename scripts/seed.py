"""
OrchestAI Seed Data Script
Generates 100 realistic employees, 10 projects, tasks, and a demo organization.
Run: python scripts/seed.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'backend'))

import uuid
import random
from datetime import datetime, timedelta, date
from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Load .env
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://orchestai:orchestai_pass@localhost:5432/orchestai_db")

from app.models.database import Base
from app.models.user import User, Organization
from app.models.employee import Employee, EmployeeSkill
from app.models.project import Project, Sprint
from app.models.task import Task, TaskDependency
from app.core.security import hash_password

fake = Faker()
random.seed(42)
Faker.seed(42)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# ─────────────────────────── DATA DEFINITIONS ───────────────────────────

DEPARTMENTS = {
    "Engineering": {
        "roles": ["Backend Engineer", "Frontend Engineer", "Full Stack Engineer", "DevOps Engineer", "AI/ML Engineer", "QA Engineer", "Mobile Engineer"],
        "skills": ["Python", "JavaScript", "TypeScript", "Go", "Java", "React", "Next.js", "FastAPI", "Django", "Node.js", "Docker", "Kubernetes", "AWS", "PostgreSQL", "Redis", "MongoDB", "TensorFlow", "PyTorch", "LangChain", "GraphQL"],
    },
    "Product": {
        "roles": ["Product Manager", "Senior Product Manager", "Principal PM", "Product Analyst"],
        "skills": ["Roadmapping", "User Research", "A/B Testing", "JIRA", "Figma", "SQL", "Mixpanel", "Amplitude", "Agile", "OKRs"],
    },
    "Design": {
        "roles": ["UI Designer", "UX Designer", "Product Designer", "Design Lead", "Brand Designer"],
        "skills": ["Figma", "Adobe XD", "Sketch", "Illustrator", "Photoshop", "Prototyping", "User Testing", "Design Systems", "Motion Design"],
    },
    "Data": {
        "roles": ["Data Scientist", "Data Engineer", "ML Engineer", "Analytics Engineer", "BI Developer"],
        "skills": ["Python", "R", "SQL", "Spark", "dbt", "Airflow", "TensorFlow", "Scikit-learn", "Tableau", "Power BI", "Snowflake", "BigQuery"],
    },
    "Marketing": {
        "roles": ["Marketing Manager", "Growth Engineer", "Content Strategist", "SEO Specialist", "Paid Ads Manager"],
        "skills": ["SEO", "Google Ads", "HubSpot", "Salesforce", "Copywriting", "Analytics", "Email Marketing", "A/B Testing", "Social Media"],
    },
    "Sales": {
        "roles": ["Account Executive", "Sales Engineer", "Customer Success Manager", "BDR", "VP Sales"],
        "skills": ["Salesforce", "HubSpot", "Negotiation", "Product Demo", "CRM", "Pipeline Management", "B2B Sales"],
    },
    "HR": {
        "roles": ["HR Manager", "Recruiter", "People Ops", "Talent Acquisition", "HR Business Partner"],
        "skills": ["Greenhouse", "Lever", "Workday", "Performance Management", "Compensation", "HRIS", "Onboarding"],
    },
}

SENIORITY_LEVELS = ["junior", "mid", "senior", "lead", "principal"]
SENIORITY_EXP = {"junior": (0.5, 2), "mid": (2, 5), "senior": (5, 10), "lead": (8, 15), "principal": (12, 20)}
SENIORITY_PERF = {"junior": (60, 80), "mid": (65, 85), "senior": (70, 92), "lead": (75, 95), "principal": (80, 98)}

TIMEZONES = ["UTC", "US/Eastern", "US/Pacific", "US/Central", "Europe/London", "Europe/Berlin", "Asia/Kolkata", "Asia/Singapore", "Australia/Sydney"]
SALARY_BANDS = ["junior", "mid", "senior", "staff", "principal"]

AVAILABILITY_WEIGHTS = {
    "available": 0.55,
    "busy": 0.30,
    "on_leave": 0.10,
    "unavailable": 0.05,
}

PROJECT_NAMES = [
    "AI Recruitment Platform",
    "Real-Time Analytics Dashboard",
    "Mobile Commerce App",
    "DevOps Automation Suite",
    "Customer Data Platform",
    "ML Model Serving Infrastructure",
    "Enterprise SSO & RBAC",
    "Multi-Region Microservices Migration",
    "AI-Powered CRM",
    "Payment Processing Gateway",
]

PROJECT_CATEGORIES = ["web_app", "ml_platform", "mobile_app", "devops", "data_platform", "api_service", "infrastructure"]

TASK_TEMPLATES = {
    "Engineering": [
        "Design database schema",
        "Implement REST API endpoints",
        "Set up CI/CD pipeline",
        "Write unit tests",
        "Code review & refactoring",
        "Performance optimization",
        "Security audit",
        "API documentation",
        "Integration with third-party services",
        "Deploy to staging environment",
    ],
    "Product": [
        "Define product requirements",
        "Create user stories",
        "Prioritize backlog",
        "Conduct user interviews",
        "Analyze feature metrics",
        "Write PRD",
        "Stakeholder alignment meeting",
        "Competitive analysis",
    ],
    "Design": [
        "Create wireframes",
        "Design high-fidelity mockups",
        "Build component library",
        "Conduct usability testing",
        "Design system update",
        "Create design spec",
    ],
}


def weighted_choice(choices: dict):
    items = list(choices.keys())
    weights = list(choices.values())
    return random.choices(items, weights=weights, k=1)[0]


def random_workload(availability: str) -> float:
    if availability == "available":
        return random.uniform(20, 70)
    elif availability == "busy":
        return random.uniform(70, 100)
    elif availability == "on_leave":
        return 0.0
    else:
        return 0.0


def generate_avatar(name: str, idx: int) -> str:
    styles = ["adventurer", "avataaars", "bottts", "fun-emoji", "lorelei", "micah", "miniavs", "notionists", "open-peeps", "personas"]
    style = styles[idx % len(styles)]
    seed = name.replace(" ", "")
    return f"https://api.dicebear.com/7.x/{style}/svg?seed={seed}"


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("🌱 Starting OrchestAI seed process...")

    # ──── Organization ────
    org = Organization(
        id=uuid.uuid4(),
        name="TechCorp Global",
        slug="techcorp-global",
        domain="techcorp.com",
        plan="enterprise",
        max_employees=500,
        is_active=True,
    )
    db.add(org)
    db.flush()
    print(f"✅ Created organization: {org.name}")

    # ──── Admin User ────
    admin_user = User(
        id=uuid.uuid4(),
        organization_id=org.id,
        email="admin@techcorp.com",
        hashed_password=hash_password("Admin@123"),
        full_name="Sarah Mitchell",
        role="admin",
        is_active=True,
        is_verified=True,
        avatar_url=generate_avatar("Sarah Mitchell", 0),
    )
    db.add(admin_user)

    # ──── Manager User ────
    manager_user = User(
        id=uuid.uuid4(),
        organization_id=org.id,
        email="manager@techcorp.com",
        hashed_password=hash_password("Manager@123"),
        full_name="James Chen",
        role="manager",
        is_active=True,
        is_verified=True,
        avatar_url=generate_avatar("James Chen", 1),
    )
    db.add(manager_user)
    db.flush()
    print("✅ Created demo users (admin@techcorp.com / Admin@123)")

    # ──── 100 Employees ────
    employees = []
    dept_names = list(DEPARTMENTS.keys())

    # Distribute: Engineering-heavy (realistic company)
    dept_distribution = {
        "Engineering": 45,
        "Product": 10,
        "Design": 10,
        "Data": 12,
        "Marketing": 8,
        "Sales": 8,
        "HR": 7,
    }

    employee_idx = 0
    for dept, count in dept_distribution.items():
        dept_info = DEPARTMENTS[dept]
        for i in range(count):
            seniority = random.choices(
                SENIORITY_LEVELS,
                weights=[0.20, 0.35, 0.30, 0.10, 0.05],
                k=1
            )[0]
            exp_range = SENIORITY_EXP[seniority]
            perf_range = SENIORITY_PERF[seniority]
            availability = weighted_choice(AVAILABILITY_WEIGHTS)
            workload = random_workload(availability)

            name = fake.name()
            role = random.choice(dept_info["roles"])
            skills = random.sample(dept_info["skills"], min(random.randint(3, 8), len(dept_info["skills"])))
            hire_date = fake.date_between(start_date="-8y", end_date="today")

            emp = Employee(
                id=uuid.uuid4(),
                organization_id=org.id,
                full_name=name,
                email=fake.unique.email(),
                department=dept,
                role=role,
                seniority=seniority,
                experience_years=round(random.uniform(*exp_range), 1),
                tech_stack=skills,
                current_workload_percentage=round(workload, 1),
                weekly_capacity_hours=random.choice([32, 40, 40, 40, 40]),
                availability_status=availability,
                performance_score=round(random.uniform(*perf_range), 1),
                salary_band=seniority,
                timezone=random.choice(TIMEZONES),
                location=f"{fake.city()}, {fake.country()}",
                avatar_url=generate_avatar(name, employee_idx),
                bio=f"{seniority.capitalize()} {role} with {exp_range[0]:.0f}+ years of experience in {dept}.",
                is_active=True,
                hire_date=datetime.combine(hire_date, datetime.min.time()),
            )
            db.add(emp)
            employees.append(emp)
            db.flush()

            # Add skills
            for j, skill in enumerate(skills):
                db.add(EmployeeSkill(
                    id=uuid.uuid4(),
                    employee_id=emp.id,
                    skill_name=skill,
                    category="Technical" if dept in ["Engineering", "Data"] else "Domain",
                    proficiency=random.randint(2, 5),
                    years_experience=round(random.uniform(0.5, min(exp_range[1], 6)), 1),
                    is_primary=(j == 0),
                ))

            employee_idx += 1

    db.flush()
    print(f"✅ Created {len(employees)} employees across {len(dept_distribution)} departments")

    # ──── 10 Projects ────
    projects = []
    statuses = ["planning", "active", "active", "active", "paused", "completed", "active", "active", "planning", "active"]
    for i, proj_name in enumerate(PROJECT_NAMES):
        start = fake.date_between(start_date="-6m", end_date="-1m")
        end = fake.date_between(start_date="today", end_date="+6m")
        completion = random.uniform(0, 100) if statuses[i] == "active" else (100 if statuses[i] == "completed" else random.uniform(0, 20))

        proj = Project(
            id=uuid.uuid4(),
            organization_id=org.id,
            created_by_id=admin_user.id,
            name=proj_name,
            description=f"Enterprise-grade {proj_name.lower()} for TechCorp Global. Built with modern architecture and AI-powered features.",
            status=statuses[i],
            priority=random.choice(["low", "medium", "high", "critical"]),
            complexity=random.choice(["medium", "complex", "enterprise"]),
            category=PROJECT_CATEGORIES[i % len(PROJECT_CATEGORIES)],
            start_date=start,
            end_date=end,
            deadline=datetime.combine(end, datetime.min.time()),
            estimated_hours=random.randint(200, 2000),
            actual_hours=random.randint(50, 500),
            completion_percentage=round(completion, 1),
            budget=random.choice([50000, 100000, 150000, 200000, 500000]),
            spent_budget=random.randint(10000, 80000),
            ai_risk_score=round(random.uniform(10, 80), 1),
            tech_stack=random.sample(["Python", "React", "PostgreSQL", "Docker", "FastAPI", "TypeScript", "Redis", "Kubernetes"], 4),
            tags=[fake.word(), fake.word()],
        )
        db.add(proj)
        projects.append(proj)
        db.flush()

        # Sprint for each project
        sprint = Sprint(
            id=uuid.uuid4(),
            project_id=proj.id,
            name=f"Sprint 1 - Foundation",
            goal="Set up core infrastructure and initial features",
            sprint_number=1,
            status="active" if proj.status == "active" else "completed",
            start_date=start,
            end_date=start + timedelta(days=14),
            velocity=random.uniform(15, 35),
            capacity_hours=random.uniform(60, 120),
        )
        db.add(sprint)
        db.flush()

        # Tasks for each project
        task_list = []
        eng_employees = [e for e in employees if e.department == "Engineering"]
        task_names = TASK_TEMPLATES.get("Engineering", []) + TASK_TEMPLATES.get("Product", [])

        for j in range(random.randint(8, 15)):
            assignee = random.choice(eng_employees) if random.random() > 0.2 else None
            t_status = random.choices(
                ["todo", "in_progress", "review", "done", "blocked"],
                weights=[0.25, 0.25, 0.15, 0.25, 0.10],
            )[0]

            task = Task(
                id=uuid.uuid4(),
                project_id=proj.id,
                sprint_id=sprint.id,
                assigned_employee_id=assignee.id if assignee else None,
                created_by_id=admin_user.id,
                title=random.choice(task_names) + f" - {proj_name[:20]}",
                description=fake.paragraph(nb_sentences=2),
                task_type=random.choice(["task", "story", "bug"]),
                status=t_status,
                priority=random.choice(["low", "medium", "high", "critical"]),
                estimated_hours=random.choice([2, 4, 8, 16, 24]),
                actual_hours=random.uniform(0, 20) if t_status in ["done", "in_progress"] else 0,
                story_points=random.choice([1, 2, 3, 5, 8, 13]),
                completion_percentage=100 if t_status == "done" else random.uniform(0, 90) if t_status == "in_progress" else 0,
                ai_risk_score=round(random.uniform(5, 70), 1),
                dag_position_x=float(j * 200),
                dag_position_y=float((j % 3) * 150),
                is_blocked=(t_status == "blocked"),
                labels=[fake.word()],
                started_at=datetime.utcnow() - timedelta(days=random.randint(1, 10)) if t_status in ["in_progress", "done"] else None,
                completed_at=datetime.utcnow() - timedelta(days=random.randint(0, 5)) if t_status == "done" else None,
            )
            db.add(task)
            task_list.append(task)

        db.flush()

        # Add task dependencies (DAG edges)
        for j in range(1, len(task_list)):
            # Each task depends on the previous one (simple chain) with some skips
            if random.random() > 0.4:
                dep_idx = random.randint(max(0, j - 3), j - 1)
                db.add(TaskDependency(
                    id=uuid.uuid4(),
                    task_id=task_list[j].id,
                    depends_on_id=task_list[dep_idx].id,
                ))

        db.flush()

    print(f"✅ Created {len(projects)} projects with tasks and DAG dependencies")

    db.commit()
    print("\n" + "="*50)
    print("🚀 OrchestAI seed complete!")
    print("="*50)
    print(f"\n📧 Admin login:   admin@techcorp.com / Admin@123")
    print(f"📧 Manager login: manager@techcorp.com / Manager@123")
    print(f"\n🌐 API Docs: http://localhost:8000/api/docs")
    print(f"🌐 Frontend: http://localhost:3000")
    print("="*50)
    db.close()


if __name__ == "__main__":
    main()
