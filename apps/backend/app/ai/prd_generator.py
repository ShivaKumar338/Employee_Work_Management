"""
AI PRD Generator
Uses LLM to generate full Product Requirements Documents from a natural language description.
"""
import json
from typing import AsyncGenerator
from app.core.config import settings

try:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
except ImportError:
    client = None

PRD_SYSTEM_PROMPT = """You are a senior product manager and solutions architect at a top-tier tech company.
When given a product idea, generate a comprehensive Product Requirements Document (PRD) in JSON format.

Always return valid JSON with this exact structure:
{
  "title": "string",
  "executive_summary": "string",
  "problem_statement": "string",
  "goals_and_objectives": ["string"],
  "target_users": ["string"],
  "features": [
    {
      "name": "string",
      "description": "string",
      "priority": "must_have|should_have|nice_to_have",
      "estimated_effort": "string"
    }
  ],
  "architecture": {
    "overview": "string",
    "frontend": "string",
    "backend": "string",
    "database": "string",
    "infrastructure": "string"
  },
  "database_schema": [
    {
      "table_name": "string",
      "fields": ["string"],
      "description": "string"
    }
  ],
  "api_endpoints": [
    {
      "method": "string",
      "path": "string",
      "description": "string"
    }
  ],
  "sprint_plan": [
    {
      "sprint_number": 1,
      "name": "string",
      "duration_weeks": 2,
      "goals": ["string"],
      "tasks": ["string"]
    }
  ],
  "team_requirements": [
    {
      "role": "string",
      "count": 1,
      "skills": ["string"],
      "duration_months": 3
    }
  ],
  "timeline": {
    "total_duration": "string",
    "phases": [
      {
        "name": "string",
        "duration": "string",
        "description": "string"
      }
    ]
  },
  "risks": [
    {
      "risk": "string",
      "probability": "high|medium|low",
      "impact": "high|medium|low",
      "mitigation": "string"
    }
  ],
  "dependencies": ["string"],
  "cost_estimate": {
    "development": "string",
    "infrastructure_monthly": "string",
    "total_6_months": "string",
    "notes": "string"
  },
  "success_metrics": ["string"]
}"""


async def generate_prd(description: str, additional_context: dict = None) -> dict:
    """Generate a full PRD from a natural language description."""
    context = ""
    if additional_context:
        context = f"\n\nAdditional context: {json.dumps(additional_context)}"

    if client and not settings.AI_MOCK_MODE:
        try:
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": PRD_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Generate a PRD for: {description}{context}"}
                ],
                temperature=0.7,
                response_format={"type": "json_object"},
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return _mock_prd(description)
    else:
        return _mock_prd(description)


def _mock_prd(description: str) -> dict:
    """Return a realistic mock PRD when OpenAI is not available."""
    return {
        "title": f"PRD: {description[:60]}",
        "executive_summary": f"This document outlines the requirements for building {description}. The platform will serve enterprise customers with scalable, AI-powered features.",
        "problem_statement": "Current solutions lack intelligent automation and real-time insights, leading to inefficiencies and missed opportunities.",
        "goals_and_objectives": [
            "Reduce manual effort by 60% through AI automation",
            "Improve team productivity by 40%",
            "Achieve 99.9% uptime SLA",
            "Launch MVP within 3 months",
        ],
        "target_users": ["Enterprise CTOs", "Engineering Managers", "HR Directors", "Project Managers"],
        "features": [
            {"name": "AI-Powered Dashboard", "description": "Real-time analytics and insights", "priority": "must_have", "estimated_effort": "3 weeks"},
            {"name": "User Management", "description": "RBAC-based user and team management", "priority": "must_have", "estimated_effort": "2 weeks"},
            {"name": "Automated Reporting", "description": "AI-generated weekly reports", "priority": "should_have", "estimated_effort": "2 weeks"},
            {"name": "API Integrations", "description": "Slack, Jira, GitHub integrations", "priority": "nice_to_have", "estimated_effort": "3 weeks"},
        ],
        "architecture": {
            "overview": "Microservices architecture with API gateway, event-driven messaging, and AI inference layer",
            "frontend": "Next.js 15 with TypeScript, TailwindCSS, and real-time WebSocket updates",
            "backend": "FastAPI with async processing, PostgreSQL, Redis caching",
            "database": "PostgreSQL with read replicas, Redis for caching and queues",
            "infrastructure": "Kubernetes on AWS EKS with auto-scaling and multi-region failover",
        },
        "database_schema": [
            {"table_name": "users", "fields": ["id", "email", "role", "org_id", "created_at"], "description": "Platform users"},
            {"table_name": "organizations", "fields": ["id", "name", "plan", "max_seats"], "description": "Multi-tenant organizations"},
            {"table_name": "analytics_events", "fields": ["id", "user_id", "event_type", "metadata", "timestamp"], "description": "Event tracking"},
        ],
        "api_endpoints": [
            {"method": "POST", "path": "/api/auth/login", "description": "User authentication"},
            {"method": "GET", "path": "/api/dashboard", "description": "Dashboard metrics"},
            {"method": "POST", "path": "/api/ai/analyze", "description": "AI analysis endpoint"},
        ],
        "sprint_plan": [
            {"sprint_number": 1, "name": "Foundation", "duration_weeks": 2, "goals": ["Setup infrastructure", "Auth system"], "tasks": ["DB schema", "JWT auth", "CI/CD pipeline"]},
            {"sprint_number": 2, "name": "Core Features", "duration_weeks": 2, "goals": ["Core API", "Basic UI"], "tasks": ["REST APIs", "Dashboard UI", "User management"]},
            {"sprint_number": 3, "name": "AI Integration", "duration_weeks": 2, "goals": ["AI features", "Analytics"], "tasks": ["LLM integration", "Analytics engine", "Real-time updates"]},
        ],
        "team_requirements": [
            {"role": "Backend Engineer", "count": 2, "skills": ["Python", "FastAPI", "PostgreSQL"], "duration_months": 4},
            {"role": "Frontend Engineer", "count": 2, "skills": ["React", "TypeScript", "Next.js"], "duration_months": 4},
            {"role": "DevOps Engineer", "count": 1, "skills": ["Docker", "Kubernetes", "AWS"], "duration_months": 4},
            {"role": "AI Engineer", "count": 1, "skills": ["Python", "OpenAI", "LangChain"], "duration_months": 3},
            {"role": "Product Manager", "count": 1, "skills": ["Agile", "User Research", "Roadmapping"], "duration_months": 4},
        ],
        "timeline": {
            "total_duration": "4 months",
            "phases": [
                {"name": "Discovery & Design", "duration": "2 weeks", "description": "Requirements, wireframes, architecture"},
                {"name": "Development", "duration": "10 weeks", "description": "Frontend, backend, AI features"},
                {"name": "Testing & QA", "duration": "2 weeks", "description": "Integration testing, security audit"},
                {"name": "Launch", "duration": "2 weeks", "description": "Deployment, monitoring, documentation"},
            ],
        },
        "risks": [
            {"risk": "AI model quality", "probability": "medium", "impact": "high", "mitigation": "Implement human-in-the-loop validation"},
            {"risk": "Scope creep", "probability": "high", "impact": "medium", "mitigation": "Strict sprint planning and change management"},
            {"risk": "Database scalability", "probability": "low", "impact": "high", "mitigation": "Design with horizontal scaling from day 1"},
        ],
        "dependencies": ["OpenAI API access", "PostgreSQL cluster", "Kubernetes cluster", "SMTP service", "Domain and SSL certificates"],
        "cost_estimate": {
            "development": "$120,000 - $180,000",
            "infrastructure_monthly": "$2,000 - $5,000",
            "total_6_months": "$132,000 - $210,000",
            "notes": "Estimates based on senior engineer rates ($120-150/hr). Infrastructure scales with usage.",
        },
        "success_metrics": [
            "DAU/MAU ratio > 40%",
            "API response time < 200ms p95",
            "Customer NPS > 50",
            "Zero critical security vulnerabilities",
        ],
    }
