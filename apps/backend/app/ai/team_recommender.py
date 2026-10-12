"""
AI Team Recommender Engine
Embedding-based skill matching with workload and performance weighting.
"""
import json
import math
import random
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.employee import Employee
from app.core.config import settings

try:
    import openai
    OPENAI_AVAILABLE = bool(settings.OPENAI_API_KEY)
except ImportError:
    OPENAI_AVAILABLE = False


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


def skill_overlap_score(employee_skills: List[str], required_skills: List[str]) -> float:
    """Simple set-based skill overlap score."""
    if not required_skills:
        return 0.5
    emp_set = {s.lower() for s in employee_skills}
    req_set = {s.lower() for s in required_skills}
    overlap = len(emp_set & req_set)
    return min(overlap / len(req_set), 1.0)


def availability_score(workload_pct: float, status: str) -> float:
    """Convert workload % to availability score."""
    if status == "on_leave" or status == "unavailable":
        return 0.0
    if status == "available":
        return max(0.0, 1.0 - (workload_pct / 100.0))
    return max(0.0, 1.0 - (workload_pct / 120.0))  # busy employees penalized


def compute_employee_score(
    employee: Employee,
    required_skills: List[str],
    role_target: str,
    query_embedding: Optional[List[float]] = None,
) -> float:
    """
    Composite score formula:
    score = 0.35 * skill_similarity
          + 0.25 * availability
          + 0.20 * performance
          + 0.10 * role_match
          + 0.10 * experience
    """
    emp_skills = employee.tech_stack or []

    # Skill similarity (embedding or text-based fallback)
    if query_embedding and employee.ai_skill_embedding:
        try:
            emb = employee.ai_skill_embedding
            if isinstance(emb, str):
                emb = json.loads(emb)
            skill_sim = (cosine_similarity(query_embedding, emb) + 1) / 2  # normalize to 0-1
        except Exception:
            skill_sim = skill_overlap_score(emp_skills, required_skills)
    else:
        skill_sim = skill_overlap_score(emp_skills, required_skills)

    # Availability score
    avail = availability_score(employee.current_workload_percentage or 0, employee.availability_status or "available")

    # Performance (normalized 0-1)
    perf = (employee.performance_score or 75) / 100.0

    # Role match
    role_match = 1.0 if role_target.lower() in (employee.role or "").lower() else 0.3

    # Experience (capped at 15 years = 1.0)
    exp = min((employee.experience_years or 0) / 15.0, 1.0)

    return (
        0.35 * skill_sim
        + 0.25 * avail
        + 0.20 * perf
        + 0.10 * role_match
        + 0.10 * exp
    )


def recommend_team(
    db: Session,
    organization_id: str,
    project_description: str,
    required_roles: List[Dict[str, Any]],
    required_skills: List[str],
    budget_constraint: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Main team recommendation function.
    Returns a confidence-scored list of employee recommendations.
    """
    employees = (
        db.query(Employee)
        .filter(
            Employee.organization_id == organization_id,
            Employee.is_active == True,
            Employee.availability_status.in_(["available", "busy"])
        )
        .all()
    )

    recommendations = []
    used_ids = set()

    for role_req in required_roles:
        role_name = role_req.get("role", "Engineer")
        count = role_req.get("count", 1)
        role_skills = role_req.get("skills", required_skills)

        candidates = []
        for emp in employees:
            if str(emp.id) in used_ids:
                continue
            score = compute_employee_score(emp, role_skills, role_name)
            candidates.append((emp, score))

        candidates.sort(key=lambda x: x[1], reverse=True)
        selected = candidates[:count]

        for emp, score in selected:
            used_ids.add(str(emp.id))
            confidence = min(int(score * 100), 99)
            recommendations.append({
                "employee_id": str(emp.id),
                "employee_name": emp.full_name,
                "role": role_name,
                "department": emp.department,
                "current_role": emp.role,
                "confidence": confidence,
                "workload_percentage": emp.current_workload_percentage,
                "availability": emp.availability_status,
                "performance_score": emp.performance_score,
                "skills": emp.tech_stack or [],
                "experience_years": emp.experience_years,
                "reasoning": _generate_reasoning(emp, role_name, score, role_skills),
            })

    # Overall team confidence
    team_confidence = (
        int(sum(r["confidence"] for r in recommendations) / len(recommendations))
        if recommendations else 0
    )

    return {
        "recommended_team": recommendations,
        "team_confidence": team_confidence,
        "total_workload_impact": sum(
            r["workload_percentage"] for r in recommendations
        ) / max(len(recommendations), 1),
        "warnings": _generate_warnings(recommendations),
    }


def _generate_reasoning(employee: Employee, role: str, score: float, required_skills: List[str]) -> str:
    emp_skills = set(s.lower() for s in (employee.tech_stack or []))
    req_skills = set(s.lower() for s in required_skills)
    matched = emp_skills & req_skills
    return (
        f"{employee.full_name} is a strong {role} candidate with {employee.experience_years:.0f} years of experience. "
        f"Matched skills: {', '.join(matched) if matched else 'general expertise'}. "
        f"Current workload: {employee.current_workload_percentage:.0f}%. "
        f"Performance score: {employee.performance_score:.0f}/100."
    )


def _generate_warnings(recommendations: List[Dict]) -> List[str]:
    warnings = []
    overloaded = [r for r in recommendations if r["workload_percentage"] > 70]
    if overloaded:
        names = ", ".join(r["employee_name"] for r in overloaded)
        warnings.append(f"High workload detected for: {names}. Consider reducing their other assignments.")
    low_conf = [r for r in recommendations if r["confidence"] < 60]
    if low_conf:
        warnings.append("Some team members have low confidence scores. Consider skill gap training or external hiring.")
    return warnings
