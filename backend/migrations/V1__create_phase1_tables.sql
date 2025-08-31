-- Phase 1 Database Tables Migration
-- Creates the core tables for AI manga generation service
-- Based on database design specification version 1.0

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- ============================================================================
-- 1. USERS TABLE
-- ============================================================================

CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    account_type VARCHAR(20) NOT NULL DEFAULT 'free',
    firebase_claims JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT check_account_type_valid 
        CHECK (account_type IN ('free', 'premium', 'admin'))
);

-- Users table indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_account_type ON users(account_type);
CREATE INDEX idx_users_created_at ON users(created_at);

-- ============================================================================
-- 2. MANGA PROJECTS TABLE
-- ============================================================================

CREATE TABLE manga_projects (
    project_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    metadata JSONB,
    settings JSONB,
    total_pages INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    
    -- Constraints
    CONSTRAINT check_project_status_valid 
        CHECK (status IN ('draft', 'processing', 'completed', 'failed', 'archived')),
    CONSTRAINT check_total_pages_positive 
        CHECK (total_pages IS NULL OR total_pages > 0)
);

-- Manga projects table indexes
CREATE INDEX idx_projects_user_id ON manga_projects(user_id);
CREATE INDEX idx_projects_status ON manga_projects(status);
CREATE INDEX idx_projects_created_at ON manga_projects(created_at DESC);
CREATE INDEX idx_projects_expires_at ON manga_projects(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX idx_projects_user_status_created ON manga_projects(user_id, status, created_at DESC);

-- JSONB and full-text search indexes
CREATE INDEX idx_projects_metadata_gin ON manga_projects USING GIN (metadata);
CREATE INDEX idx_projects_title_fts ON manga_projects USING GIN (to_tsvector('english', title));

-- ============================================================================
-- 3. GENERATION REQUESTS TABLE
-- ============================================================================

CREATE TABLE generation_requests (
    request_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES manga_projects(project_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    input_text TEXT NOT NULL,
    request_settings JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(20) NOT NULL DEFAULT 'queued',
    current_module INTEGER NOT NULL DEFAULT 0,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    retry_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT check_request_status_valid 
        CHECK (status IN ('queued', 'processing', 'completed', 'failed', 'cancelled')),
    CONSTRAINT check_current_module_range 
        CHECK (current_module >= 0 AND current_module <= 7),
    CONSTRAINT check_retry_count_non_negative 
        CHECK (retry_count >= 0),
    CONSTRAINT check_timestamps_logical_order 
        CHECK (started_at IS NULL OR completed_at IS NULL OR started_at <= completed_at)
);

-- Generation requests table indexes
CREATE INDEX idx_requests_project_id ON generation_requests(project_id);
CREATE INDEX idx_requests_user_id ON generation_requests(user_id);
CREATE INDEX idx_requests_status ON generation_requests(status);
CREATE INDEX idx_requests_current_module ON generation_requests(current_module);
CREATE INDEX idx_requests_created_at ON generation_requests(created_at DESC);
CREATE INDEX idx_requests_status_created ON generation_requests(status, created_at DESC);

-- Specialized indexes for queue processing
CREATE INDEX idx_requests_queue ON generation_requests(status, created_at) WHERE status = 'queued';
CREATE INDEX idx_requests_active ON generation_requests(user_id, created_at DESC) 
    WHERE status IN ('queued', 'processing');

-- ============================================================================
-- 4. PROCESSING MODULES TABLE
-- ============================================================================

CREATE TABLE processing_modules (
    module_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id UUID NOT NULL REFERENCES generation_requests(request_id) ON DELETE CASCADE,
    module_number INTEGER NOT NULL,
    module_name VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    checkpoint_data JSONB,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT check_module_status_valid 
        CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'skipped')),
    CONSTRAINT check_module_number_range 
        CHECK (module_number >= 1 AND module_number <= 7),
    CONSTRAINT check_module_name_valid 
        CHECK (module_name IN (
            'concept_analysis',
            'character_visual', 
            'plot_structure',
            'name_generation',
            'scene_generation',
            'text_placement',
            'final_integration'
        )),
    CONSTRAINT check_duration_non_negative 
        CHECK (duration_ms IS NULL OR duration_ms >= 0),
    CONSTRAINT check_module_timestamps_logical_order 
        CHECK (started_at IS NULL OR completed_at IS NULL OR started_at <= completed_at),
    
    -- Unique constraint for request-module combination
    CONSTRAINT uk_modules_request_number UNIQUE (request_id, module_number)
);

-- Processing modules table indexes
CREATE INDEX idx_modules_request_number ON processing_modules(request_id, module_number);
CREATE INDEX idx_modules_status ON processing_modules(status);
CREATE INDEX idx_modules_module_name ON processing_modules(module_name);
CREATE INDEX idx_modules_duration ON processing_modules(duration_ms);
CREATE INDEX idx_modules_created_at ON processing_modules(created_at DESC);

-- Performance and queue optimization indexes
CREATE INDEX idx_modules_performance ON processing_modules(module_name, status, duration_ms);
CREATE INDEX idx_modules_pending ON processing_modules(request_id, module_number) WHERE status = 'pending';

-- ============================================================================
-- 5. TRIGGERS FOR UPDATED_AT
-- ============================================================================

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers to all tables
CREATE TRIGGER trigger_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_manga_projects_updated_at
    BEFORE UPDATE ON manga_projects
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_generation_requests_updated_at
    BEFORE UPDATE ON generation_requests
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_processing_modules_updated_at
    BEFORE UPDATE ON processing_modules
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 6. ROW LEVEL SECURITY (RLS) SETUP
-- ============================================================================

-- Enable RLS on user-specific tables
ALTER TABLE manga_projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE generation_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE processing_modules ENABLE ROW LEVEL SECURITY;

-- Create policies for user isolation
CREATE POLICY project_isolation ON manga_projects
    FOR ALL
    USING (user_id = current_setting('app.user_id', true)::UUID);

CREATE POLICY admin_project_access ON manga_projects
    FOR ALL
    USING (current_setting('app.user_role', true) = 'admin');

CREATE POLICY request_isolation ON generation_requests
    FOR ALL
    USING (user_id = current_setting('app.user_id', true)::UUID);

CREATE POLICY admin_request_access ON generation_requests
    FOR ALL
    USING (current_setting('app.user_role', true) = 'admin');

-- Note: processing_modules inherits access control through generation_requests relationship

-- ============================================================================
-- 7. PERFORMANCE OPTIMIZATION VIEWS
-- ============================================================================

-- View for active request monitoring
CREATE VIEW active_requests AS
SELECT 
    r.request_id,
    r.user_id,
    r.project_id,
    r.status,
    r.current_module,
    r.started_at,
    r.retry_count,
    p.title as project_title,
    u.email as user_email,
    u.account_type,
    COUNT(m.module_id) as completed_modules
FROM generation_requests r
    LEFT JOIN manga_projects p ON r.project_id = p.project_id
    LEFT JOIN users u ON r.user_id = u.user_id
    LEFT JOIN processing_modules m ON r.request_id = m.request_id AND m.status = 'completed'
WHERE r.status IN ('queued', 'processing')
GROUP BY r.request_id, r.user_id, r.project_id, r.status, r.current_module, 
         r.started_at, r.retry_count, p.title, u.email, u.account_type;

-- View for user project summary
CREATE VIEW user_project_summary AS
SELECT 
    u.user_id,
    u.email,
    u.account_type,
    COUNT(p.project_id) as total_projects,
    COUNT(CASE WHEN p.status = 'completed' THEN 1 END) as completed_projects,
    COUNT(CASE WHEN p.status = 'processing' THEN 1 END) as processing_projects,
    MAX(p.created_at) as last_project_created,
    SUM(COALESCE(p.total_pages, 0)) as total_pages_generated
FROM users u
    LEFT JOIN manga_projects p ON u.user_id = p.user_id 
        AND (p.expires_at IS NULL OR p.expires_at > NOW())
GROUP BY u.user_id, u.email, u.account_type;

-- ============================================================================
-- 8. INITIAL DATA
-- ============================================================================

-- Insert system admin user (if not exists)
INSERT INTO users (user_id, email, display_name, account_type, firebase_claims)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'admin@manga-ai.com',
    'System Administrator',
    'admin',
    '{"role": "admin", "permissions": ["all"]}'
) ON CONFLICT (email) DO NOTHING;

-- ============================================================================
-- Migration completed successfully
-- ============================================================================