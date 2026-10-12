# OrchestAI — Local Setup Guide
## Step-by-step guide to run the platform on your machine

---

## Prerequisites

| Tool | Min Version | Download |
|------|------------|---------|
| Python | 3.11+ | https://python.org |
| Node.js | 18+ | https://nodejs.org |
| PostgreSQL | 14+ | https://postgresql.org |
| Git | any | https://git-scm.com |
| Redis | 7+ (optional) | https://redis.io |

---

## Step 1 — Clone the project

```bash
git clone <your-repo-url> Empl_AI
cd Empl_AI
```

---

## Step 2 — Set up PostgreSQL

### 2a. Create the database & user

Open **pgAdmin** or **psql** and run:

```sql
-- Create the user (skip if you want to use existing 'postgres' superuser)
CREATE USER orchestai WITH PASSWORD 'orchestai_pass';

-- Create the database
CREATE DATABASE orchestai_db OWNER orchestai;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE orchestai_db TO orchestai;
```

> **Tip:** If you already have a `postgres` superuser, you can simplify:  
> `CREATE DATABASE orchestai_db;`  
> and set `DATABASE_URL=postgresql://postgres:YOUR_PG_PASSWORD@localhost:5432/orchestai_db`

### 2b. Initialize schema

```bash
# From project root
psql -U orchestai -d orchestai_db -f database/init_db.sql

# Or using the postgres superuser
psql -U postgres -d orchestai_db -f database/init_db.sql
```

---

## Step 3 — Configure Environment Variables

```bash
# Copy the example file
cp .env.example .env
```

Open `.env` and update **at minimum** these values:

```env
# Match the credentials you used in Step 2
DATABASE_URL=postgresql://orchestai:orchestai_pass@localhost:5432/orchestai_db

# Keep AI_MOCK_MODE=true for offline/demo use (no OpenAI key needed)
AI_MOCK_MODE=true

# Frontend URL (default is fine for localhost)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

> The backend loads `.env` from the **project root** (`Empl_AI/.env`).  
> The frontend loads `.env.local` from `apps/frontend/.env.local`.

---

## Step 4 — Set up & Run the Backend

```bash
cd apps/backend

# (Recommended) Create a virtual environment
python -m venv venv

# Activate it
# Windows PowerShell:
venv\Scripts\Activate.ps1
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the development server
# Run from the project ROOT so .env is found automatically
cd ../..
uvicorn apps.backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

> ✅ Backend should be running at **http://localhost:8000**  
> ✅ API Docs available at **http://localhost:8000/api/docs**

### Alternative: run directly from the backend folder

```bash
cd apps/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

> Make sure your `.env` is in `apps/backend/` OR the project root (the config uses `env_file = ".env"`).

---

## Step 5 — Seed Demo Data

```bash
# From project root (with venv active)
cd database
python seed_data.py
```

This creates:
- ✅ 1 organization (TechForge Inc.)
- ✅ 5 users (admin, manager, 3 leads)
- ✅ 10 employees with skills
- ✅ 3 projects (1 active MVP, 1 analytics, 1 POS planning)
- ✅ Sprints, tasks with DAG dependencies
- ✅ AI recommendations & analytics snapshots

---

## Step 6 — Set up & Run the Frontend

```bash
cd apps/frontend

# Install packages
npm install

# Create frontend env file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start dev server
npm run dev
```

> ✅ Frontend runs at **http://localhost:3000**

---

## Step 7 — Login

Open **http://localhost:3000** in your browser and log in:

| Role    | Email                    | Password   |
|---------|--------------------------|------------|
| Admin   | admin@techforge.io       | Demo1234!  |
| Manager | manager@techforge.io     | Demo1234!  |
| Lead    | alice@techforge.io       | Demo1234!  |

---

## Running Both Services Together (PowerShell)

Open **two PowerShell windows** side by side:

**Window 1 — Backend:**
```powershell
cd C:\Users\HP\Downloads\Empl_AI
# Activate venv if using one
.\apps\backend\venv\Scripts\Activate.ps1
uvicorn apps.backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

**Window 2 — Frontend:**
```powershell
cd C:\Users\HP\Downloads\Empl_AI\apps\frontend
npm run dev
```

---

## Alembic Database Migrations

After schema changes, generate and apply migrations:

```bash
cd apps/backend

# Initialize Alembic (first time only)
alembic init alembic

# Generate a new migration
alembic revision --autogenerate -m "describe your change"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

---

## Optional: Redis Setup

Redis is only needed for Celery background jobs and caching. For MVP demos, you can skip it.

```bash
# Windows — using Memurai (Redis-compatible for Windows)
# Download from: https://www.memurai.com/

# Or via WSL2 / Docker:
docker run -d -p 6379:6379 redis:7-alpine
```

---

## Optional: Full Docker Setup

```bash
# Start all services (PostgreSQL + Redis + Backend + Frontend)
docker-compose up --build

# In a separate terminal, seed the data
docker-compose exec backend python database/seed_data.py

# Stop everything
docker-compose down

# Stop and remove volumes (resets database)
docker-compose down -v
```

---

## Common Issues & Fixes

### ❌ `psycopg2` connection error
```
sqlalchemy.exc.OperationalError: could not connect to server
```
**Fix:** Make sure PostgreSQL is running and your `DATABASE_URL` credentials match.

```powershell
# Check if PostgreSQL is running (Windows)
Get-Service postgresql*
```

---

### ❌ `ModuleNotFoundError: No module named 'app'`
**Fix:** Run `uvicorn` from either the project root or `apps/backend/`, not from inside `app/`.

```bash
# Correct (from project root)
uvicorn apps.backend.app.main:app --reload

# Correct (from apps/backend)
cd apps/backend
uvicorn app.main:app --reload
```

---

### ❌ Frontend shows `Network Error` or CORS issues
**Fix:** Ensure the backend is running, and `NEXT_PUBLIC_API_URL` in `.env.local` matches.

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

### ❌ `npm install` fails
```
npm ERR! ERESOLVE unable to resolve dependency tree
```
**Fix:**
```bash
npm install --legacy-peer-deps
```

---

### ❌ Seed script fails with `ImportError`
**Fix:** Run with venv active and from the `database/` directory:
```bash
cd database
python seed_data.py
```

---

## Useful Commands Reference

```bash
# Check backend health
curl http://localhost:8000/api/health

# View all API routes
open http://localhost:8000/api/docs

# Reset DB and re-seed
psql -U postgres -d orchestai_db -f database/init_db.sql
python database/seed_data.py

# Lint frontend
cd apps/frontend && npm run lint

# Build frontend for production
cd apps/frontend && npm run build
```

---

## Deploying Frontend to Vercel

```bash
cd apps/frontend

# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

In Vercel dashboard → Project Settings → Environment Variables, add:
```
NEXT_PUBLIC_API_URL=https://your-backend-url.com
```

---

Happy hacking! 🚀 For questions, check the README or open an issue.
