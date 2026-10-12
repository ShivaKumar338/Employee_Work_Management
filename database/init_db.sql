-- =============================================================
-- OrchestAI — PostgreSQL Schema
-- Run this once to bootstrap your local database.
-- Usage:  psql -U postgres -f database/init_db.sql
-- =============================================================

-- Create database (run separately if it doesn't exist)
-- CREATE DATABASE orchestai_db;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================
-- 1. Organizations
-- =============================================================
CREATE TABLE IF NOT EXISTS organizations (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(255) NOT NULL,
    slug        VARCHAR(100) UNIQUE NOT NULL,
    domain      VARCHAR(255),
    logo_url    TEXT,
    plan        VARCHAR(50) DEFAULT 'free',       -- free | pro | enterprise
    max_employees INTEGER DEFAULT 50,
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW()
);

-- =============================================================
-- 2. Users
-- =============================================================
CREATE TABLE IF NOT EXISTS users (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id     UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email               VARCHAR(255) UNIQUE NOT NULL,
    hashed_password     VARCHAR(255),
    full_name           VARCHAR(255) NOT NULL,
    role                VARCHAR(50) DEFAULT 'employee',   -- super_admin | admin | manager | team_lead | employee
    avatar_url          TEXT,
    is_active           BOOLEAN DEFAULT TRUE,
    is_verified         BOOLEAN DEFAULT FALSE,
    oauth_provider      VARCHAR(50),
    oauth_id            VARCHAR(255),
    refresh_token_hash  VARCHAR(255),
    last_login          TIMESTAMP,
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_org   ON users(organization_id);

-- =============================================================
-- 3. Employees
-- =============================================================
CREATE TABLE IF NOT EXISTS employees (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id             UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id                     UUID REFERENCES users(id) ON DELETE SET NULL,
    manager_id                  UUID REFERENCES employees(id) ON DELETE SET NULL,

    full_name                   VARCHAR(255) NOT NULL,
    email                       VARCHAR(255) NOT NULL,
    department                  VARCHAR(100) NOT NULL,
    role                        VARCHAR(100) NOT NULL,
    seniority                   VARCHAR(50) DEFAULT 'mid',          -- junior | mid | senior | lead | principal
    experience_years            FLOAT DEFAULT 0,

    tech_stack                  JSONB DEFAULT '[]',
    current_workload_percentage FLOAT DEFAULT 0.0,
    weekly_capacity_hours       FLOAT DEFAULT 40.0,
    availability_status         VARCHAR(50) DEFAULT 'available',    -- available | busy | on_leave | unavailable
    performance_score           FLOAT DEFAULT 75.0,
    salary_band                 VARCHAR(50),
    timezone                    VARCHAR(100) DEFAULT 'UTC',
    location                    VARCHAR(255),

    avatar_url                  TEXT,
    bio                         TEXT,
    github_url                  VARCHAR(255),
    linkedin_url                VARCHAR(255),

    ai_skill_embedding          JSONB,
    ai_compatibility_score      FLOAT DEFAULT 0.0,

    is_active                   BOOLEAN DEFAULT TRUE,
    hire_date                   TIMESTAMP,
    created_at                  TIMESTAMP DEFAULT NOW(),
    updated_at                  TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_employees_email ON employees(email);
CREATE INDEX IF NOT EXISTS idx_employees_org   ON employees(organization_id);

-- =============================================================
-- 4. Employee Skills
-- =============================================================
CREATE TABLE IF NOT EXISTS employee_skills (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id      UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    skill_name       VARCHAR(100) NOT NULL,
    category         VARCHAR(100),         -- Programming Language | Framework | Tool | Soft Skill
    proficiency      INTEGER DEFAULT 3,    -- 1-5
    years_experience FLOAT DEFAULT 0,
    is_primary       BOOLEAN DEFAULT FALSE,
    created_at       TIMESTAMP DEFAULT NOW()
);

-- =============================================================
-- 5. Projects
-- =============================================================
CREATE TABLE IF NOT EXISTS projects (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id             UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_by_id               UUID REFERENCES users(id) ON DELETE SET NULL,

    name                        VARCHAR(255) NOT NULL,
    description                 TEXT,
    status                      VARCHAR(50) DEFAULT 'planning',     -- planning | active | paused | completed | cancelled
    priority                    VARCHAR(50) DEFAULT 'medium',       -- low | medium | high | critical
    complexity                  VARCHAR(50) DEFAULT 'medium',       -- simple | medium | complex | enterprise
    category                    VARCHAR(100),

    start_date                  DATE,
    end_date                    DATE,
    deadline                    TIMESTAMP,
    estimated_hours             FLOAT,
    actual_hours                FLOAT DEFAULT 0.0,

    completion_percentage       FLOAT DEFAULT 0.0,
    budget                      FLOAT,
    spent_budget                FLOAT DEFAULT 0.0,

    ai_risk_score               FLOAT DEFAULT 0.0,
    ai_complexity_score         FLOAT DEFAULT 0.0,
    ai_recommended_team_size    INTEGER,
    ai_insights                 JSONB,
    prd_content                 TEXT,

    tech_stack                  JSONB DEFAULT '[]',
    tags                        JSONB DEFAULT '[]',

    created_at                  TIMESTAMP DEFAULT NOW(),
    updated_at                  TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_projects_org ON projects(organization_id);

-- =============================================================
-- 6. Sprints
-- =============================================================
CREATE TABLE IF NOT EXISTS sprints (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    name            VARCHAR(255) NOT NULL,
    goal            TEXT,
    sprint_number   INTEGER DEFAULT 1,
    status          VARCHAR(50) DEFAULT 'planning',   -- planning | active | completed | cancelled
    start_date      DATE,
    end_date        DATE,
    velocity        FLOAT DEFAULT 0.0,
    capacity_hours  FLOAT DEFAULT 0.0,

    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- =============================================================
-- 7. Tasks
-- =============================================================
CREATE TABLE IF NOT EXISTS tasks (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id              UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    sprint_id               UUID REFERENCES sprints(id) ON DELETE SET NULL,
    assigned_employee_id    UUID REFERENCES employees(id) ON DELETE SET NULL,
    created_by_id           UUID REFERENCES users(id) ON DELETE SET NULL,
    parent_task_id          UUID REFERENCES tasks(id) ON DELETE SET NULL,

    title                   VARCHAR(500) NOT NULL,
    description             TEXT,
    task_type               VARCHAR(50) DEFAULT 'task',       -- task | bug | story | epic | subtask
    status                  VARCHAR(50) DEFAULT 'todo',       -- todo | in_progress | review | blocked | done | cancelled
    priority                VARCHAR(50) DEFAULT 'medium',     -- low | medium | high | critical

    dag_position_x          FLOAT DEFAULT 0.0,
    dag_position_y          FLOAT DEFAULT 0.0,
    is_critical_path        BOOLEAN DEFAULT FALSE,
    is_blocked              BOOLEAN DEFAULT FALSE,
    blocking_reason         TEXT,

    story_points            INTEGER,
    estimated_hours         FLOAT,
    actual_hours            FLOAT DEFAULT 0.0,
    deadline                TIMESTAMP,

    ai_risk_score           FLOAT DEFAULT 0.0,
    ai_priority_score       FLOAT DEFAULT 0.0,
    ai_complexity           VARCHAR(50),

    completion_percentage   FLOAT DEFAULT 0.0,
    labels                  JSONB DEFAULT '[]',

    started_at              TIMESTAMP,
    completed_at            TIMESTAMP,
    created_at              TIMESTAMP DEFAULT NOW(),
    updated_at              TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tasks_project  ON tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_employee ON tasks(assigned_employee_id);

-- =============================================================
-- 8. Task Dependencies (DAG edges)
-- =============================================================
CREATE TABLE IF NOT EXISTS task_dependencies (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id         UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    depends_on_id   UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    dependency_type VARCHAR(50) DEFAULT 'finish_to_start',
    created_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE (task_id, depends_on_id)
);

-- =============================================================
-- 9. Notifications
-- =============================================================
CREATE TABLE IF NOT EXISTS notifications (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title               VARCHAR(255) NOT NULL,
    message             TEXT NOT NULL,
    notification_type   VARCHAR(100) DEFAULT 'info',
    is_read             BOOLEAN DEFAULT FALSE,
    action_url          VARCHAR(500),
    metadata            JSONB,
    created_at          TIMESTAMP DEFAULT NOW()
);

-- =============================================================
-- 10. AI Recommendations
-- =============================================================
CREATE TABLE IF NOT EXISTS ai_recommendations (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id     UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    project_id          UUID REFERENCES projects(id) ON DELETE CASCADE,
    recommendation_type VARCHAR(100) NOT NULL,
    input_data          JSONB,
    output_data         JSONB,
    confidence_score    FLOAT DEFAULT 0.0,
    model_used          VARCHAR(100),
    tokens_used         FLOAT DEFAULT 0.0,
    created_by_id       UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at          TIMESTAMP DEFAULT NOW()
);

-- =============================================================
-- 11. Analytics Snapshots
-- =============================================================
CREATE TABLE IF NOT EXISTS analytics_snapshots (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    snapshot_date   TIMESTAMP NOT NULL,
    snapshot_type   VARCHAR(100) NOT NULL,    -- daily | weekly | sprint
    metrics         JSONB NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- =============================================================
-- 12. Activity Logs
-- =============================================================
CREATE TABLE IF NOT EXISTS activity_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id         UUID REFERENCES users(id) ON DELETE SET NULL,
    action          VARCHAR(255) NOT NULL,
    resource_type   VARCHAR(100),
    resource_id     VARCHAR(255),
    details         JSONB,
    ip_address      VARCHAR(50),
    user_agent      VARCHAR(500),
    created_at      TIMESTAMP DEFAULT NOW()
);

-- =============================================================
-- Trigger: auto-update updated_at columns
-- =============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DO $$
DECLARE
    t TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY['organizations','users','employees','projects','sprints','tasks']
    LOOP
        EXECUTE format('
            DROP TRIGGER IF EXISTS trg_%s_updated_at ON %s;
            CREATE TRIGGER trg_%s_updated_at
            BEFORE UPDATE ON %s
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        ', t, t, t, t);
    END LOOP;
END;
$$;

-- =============================================================
-- Done! Run seed_data.py next to populate sample data.
-- =============================================================
