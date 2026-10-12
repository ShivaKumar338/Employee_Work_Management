"""
AI Risk Analyzer & Workload Balancer
"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.employee import Employee
from app.models.project import Project
from app.models.task import Task


def analyze_project_risk(project: Project, tasks: List[Task], team: List[Employee]) -> Dict:
    """Compute an overall project risk score and breakdown."""
    risks = []
    total_risk = 0.0

    # Timeline risk
    from datetime import datetime, timedelta
    if project.deadline:
        days_remaining = (project.deadline - datetime.utcnow()).days
        if days_remaining < 7:
            risks.append({"factor": "Tight deadline", "severity": "critical", "score": 40})
            total_risk += 40
        elif days_remaining < 30:
            risks.append({"factor": "Short timeline", "severity": "high", "score": 25})
            total_risk += 25

    # Overloaded team risk
    overloaded_members = [e for e in team if (e.current_workload_percentage or 0) > 80]
    if overloaded_members:
        risk_score = min(len(overloaded_members) * 10, 30)
        risks.append({
            "factor": f"{len(overloaded_members)} team member(s) overloaded",
            "severity": "high" if risk_score > 20 else "medium",
            "score": risk_score,
        })
        total_risk += risk_score

    # Blocked tasks risk
    blocked_tasks = [t for t in tasks if t.is_blocked]
    if blocked_tasks:
        risk_score = min(len(blocked_tasks) * 5, 25)
        risks.append({
            "factor": f"{len(blocked_tasks)} task(s) blocked",
            "severity": "high" if risk_score > 15 else "medium",
            "score": risk_score,
        })
        total_risk += risk_score

    # Completion risk
    if project.completion_percentage < 30 and project.deadline:
        from datetime import datetime
        total_duration = (project.deadline - project.created_at).days if project.created_at else 90
        elapsed = (datetime.utcnow() - project.created_at).days if project.created_at else 0
        if total_duration > 0 and elapsed / total_duration > 0.5:
            risks.append({"factor": "Behind schedule", "severity": "high", "score": 20})
            total_risk += 20

    # Team size risk
    if len(team) < 2:
        risks.append({"factor": "Single point of failure (solo team)", "severity": "medium", "score": 10})
        total_risk += 10

    risk_score = min(total_risk, 100)

    return {
        "risk_score": risk_score,
        "risk_level": "critical" if risk_score > 70 else "high" if risk_score > 50 else "medium" if risk_score > 30 else "low",
        "risk_factors": risks,
        "recommendations": _risk_recommendations(risks),
    }


def _risk_recommendations(risks: List[Dict]) -> List[str]:
    recs = []
    for risk in risks:
        factor = risk["factor"]
        if "deadline" in factor.lower():
            recs.append("Consider extending the deadline or reducing scope for the current sprint.")
        if "overloaded" in factor.lower():
            recs.append("Redistribute tasks from overloaded engineers to available team members.")
        if "blocked" in factor.lower():
            recs.append("Schedule a dependency resolution meeting to unblock critical tasks.")
        if "behind" in factor.lower():
            recs.append("Conduct a sprint retrospective and re-plan remaining milestones.")
    return list(set(recs))


def balance_workload(employees: List[Employee], tasks_to_assign: int = 0) -> Dict:
    """Analyze workload distribution and suggest rebalancing."""
    if not employees:
        return {"status": "no_employees", "suggestions": []}

    workloads = [
        {
            "employee_id": str(e.id),
            "name": e.full_name,
            "workload_pct": e.current_workload_percentage or 0,
            "status": e.availability_status,
            "capacity_hours": e.weekly_capacity_hours or 40,
        }
        for e in employees
    ]

    avg_workload = sum(w["workload_pct"] for w in workloads) / len(workloads)
    overloaded = [w for w in workloads if w["workload_pct"] > 85]
    underloaded = [w for w in workloads if w["workload_pct"] < 40 and w["status"] == "available"]

    suggestions = []
    for over in overloaded:
        for under in underloaded[:2]:
            suggestions.append({
                "action": "redistribute",
                "from": over["name"],
                "to": under["name"],
                "reason": f"{over['name']} is at {over['workload_pct']:.0f}% capacity. "
                          f"{under['name']} has capacity at {under['workload_pct']:.0f}%.",
            })

    return {
        "average_workload_pct": round(avg_workload, 1),
        "overloaded_count": len(overloaded),
        "underloaded_count": len(underloaded),
        "overloaded_employees": overloaded,
        "underloaded_employees": underloaded,
        "suggestions": suggestions,
        "team_health": "critical" if len(overloaded) > len(employees) * 0.4 else "good" if avg_workload < 70 else "warning",
    }
