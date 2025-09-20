-- Complete Database Schema Creation Script
-- This script creates all necessary tables for the manga generation system

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop existing tables if they exist (to ensure clean state)
DROP TABLE IF EXISTS manga_assets CASCADE;
DROP TABLE IF EXISTS manga_projects CASCADE;
DROP TABLE IF EXISTS manga_sessions CASCADE;
DROP TABLE IF EXISTS user_refresh_tokens CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS alembic_version CASCADE;

-- Create users table (base table, referenced by others)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    google_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    avatar_url VARCHAR(512),
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_premium BOOLEAN NOT NULL DEFAULT false,
    subscription_tier VARCHAR(32) DEFAULT 'free',
    daily_generation_count INTEGER NOT NULL DEFAULT 0,
    daily_limit_reset_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create user_refresh_tokens table
CREATE TABLE user_refresh_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token TEXT NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_revoked BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create manga_sessions table
CREATE TABLE manga_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    title VARCHAR(255),
    text TEXT NOT NULL,
    ai_auto_settings BOOLEAN NOT NULL DEFAULT true,
    feedback_mode JSONB,
    options JSONB,
    estimated_completion_time TIMESTAMP WITH TIME ZONE,
    actual_completion_time TIMESTAMP WITH TIME ZONE,
    current_phase INTEGER DEFAULT 0,
    total_phases INTEGER DEFAULT 5,
    error_message TEXT,
    websocket_channel VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create manga_projects table (depends on users and manga_sessions)
CREATE TABLE manga_projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    session_id UUID REFERENCES manga_sessions(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'draft',
    description TEXT,
    project_metadata JSONB,
    settings JSONB,
    total_pages INTEGER,
    style VARCHAR(64),
    visibility VARCHAR(32) NOT NULL DEFAULT 'private',
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create manga_assets table (depends on manga_projects and manga_sessions)
CREATE TABLE manga_assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES manga_projects(id) ON DELETE CASCADE,
    session_id UUID REFERENCES manga_sessions(id) ON DELETE SET NULL,
    asset_type VARCHAR(32) NOT NULL,
    phase INTEGER NOT NULL,
    storage_path VARCHAR(512) NOT NULL,
    file_size BIGINT,
    content_type VARCHAR(100),
    asset_metadata JSONB,
    quality_score NUMERIC(4, 2),
    is_primary BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create alembic_version table for migration tracking
CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Insert current migration version
INSERT INTO alembic_version (version_num) VALUES ('0002_create_manga_projects');

-- Create indexes for performance
CREATE INDEX ix_users_email ON users(email);
CREATE INDEX ix_users_google_id ON users(google_id);
CREATE INDEX ix_user_refresh_tokens_user_id ON user_refresh_tokens(user_id);
CREATE INDEX ix_user_refresh_tokens_refresh_token ON user_refresh_tokens(refresh_token);
CREATE INDEX ix_manga_sessions_user_id ON manga_sessions(user_id);
CREATE INDEX ix_manga_sessions_status ON manga_sessions(status);
CREATE INDEX ix_manga_projects_user_id ON manga_projects(user_id);
CREATE INDEX ix_manga_projects_status ON manga_projects(status);
CREATE INDEX ix_manga_projects_session_id ON manga_projects(session_id);
CREATE INDEX ix_manga_assets_project_id ON manga_assets(project_id);
CREATE INDEX ix_manga_assets_session_id ON manga_assets(session_id);

-- Create triggers for updated_at columns
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_timestamp_users
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

CREATE TRIGGER set_timestamp_user_refresh_tokens
    BEFORE UPDATE ON user_refresh_tokens
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

CREATE TRIGGER set_timestamp_manga_sessions
    BEFORE UPDATE ON manga_sessions
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

CREATE TRIGGER set_timestamp_manga_projects
    BEFORE UPDATE ON manga_projects
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

CREATE TRIGGER set_timestamp_manga_assets
    BEFORE UPDATE ON manga_assets
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();

-- Verify table creation
\dt