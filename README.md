# OrchestAI 🤖
## AI-Powered Workforce Orchestration Platform

> **Hackathon-ready · Localhost-first · Enterprise SaaS feel**

OrchestAI is a full-stack platform that combines **FastAPI**, **Next.js 16**, **PostgreSQL**, and **AI** to intelligently manage employees, projects, and tasks — complete with DAG-based workflow visualization and AI team recommendations.

---

## ✨ Features

| Area | What's included |
|------|----------------|
| 🔐 Auth | JWT login, refresh tokens, role-based access |
| 👥 Employees | Full CRUD, skills tracking, workload percentage |
| 📁 Projects | Status, budget, AI risk score, PRD generation |
| 📋 Tasks | Kanban-style + DAG dependency graph (React Flow) |
| 🤖 AI Engine | Team recommendation, workload balance, sprint planning |
| 📊 Analytics | Charts, KPI cards, productivity metrics |
| 🔔 Real-time | WebSocket live task status updates |
| 🛒 POS | Point-of-sale module (planned) |

---

## 🗂️ Project Structure

```
Empl_AI/
├── apps/
│   ├── backend/          # FastAPI application
│   │   ├── app/
│   │   │   ├── api/      # Route handlers
│   │   │   ├── ai/       # AI & DAG engine
│   │   │   ├── core/     # Config, security
│   │   │   └── models/   # SQLAlchemy models
│   │   └── requirements.txt
│   └── frontend/         # Next.js 16 application
│       └── src/
│           ├── app/      # App Router pages
│           ├── components/
│           └── lib/
├── database/
│   ├── init_db.sql       # PostgreSQL schema
│   └── seed_data.py      # Demo data seeder
├── docs/
├── .env.example
├── docker-compose.yml    # Optional Docker setup
└── README.md
```

---

## 🚀 Quick Start (Localhost)

> **See [SETUP_GUIDE.md](./SETUP_GUIDE.md) for the full step-by-step guide.**

```bash
# 1 — Clone & enter project
cd Empl_AI

# 2 — Copy and configure environment
cp .env.example .env
# Edit .env with your PostgreSQL credentials

# 3 — Start backend
cd apps/backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# 4 — Start frontend (new terminal)
cd apps/frontend
npm install
npm run dev
```

Open **http://localhost:3000** — login with `admin@techforge.io / Demo1234!`

---

## 🛠️ Tech Stack

**Frontend** — Next.js 16, TailwindCSS v4, shadcn/ui, React Flow, Recharts, Framer Motion, Zustand  
**Backend** — FastAPI 0.115, SQLAlchemy 2, Alembic, Pydantic v2, python-jose  
**Database** — PostgreSQL 15+  
**AI** — OpenAI GPT-4o-mini (or mock mode for offline demo)  
**Optional** — Redis, Celery (background jobs)

---

## 🔑 Default Demo Credentials

| Role    | Email                    | Password   |
|---------|--------------------------|------------|
| Admin   | admin@techforge.io       | Demo1234!  |
| Manager | manager@techforge.io     | Demo1234!  |
| Lead    | alice@techforge.io       | Demo1234!  |

---

## 📡 API Reference

- **Swagger UI** → http://localhost:8000/api/docs  
- **ReDoc** → http://localhost:8000/api/redoc  
- **Health Check** → http://localhost:8000/api/health

---

## 🐳 Optional Docker

```bash
# Start everything (PostgreSQL + Redis + Backend + Frontend)
docker-compose up --build

# Stop
docker-compose down
```

---

## 📦 Deploy to Vercel (Frontend)

```bash
cd apps/frontend
npx vercel --prod
```

Set `NEXT_PUBLIC_API_URL` to your hosted backend URL in Vercel's environment variables.


