-- Complete Database Schema Fix v2
-- Ensures ALL required tables and columns exist including session_messages and session_events

DO $$
BEGIN
    -- Enable UUID extension if not exists
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

    -- Create manga_sessions table if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'manga_sessions'
    ) THEN
        CREATE TABLE manga_sessions (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            request_id UUID NOT NULL UNIQUE DEFAULT uuid_generate_v4(),
            user_id UUID,
            project_id UUID,
            status VARCHAR(32) NOT NULL DEFAULT 'queued',
            current_phase INTEGER,
            retry_count INTEGER NOT NULL DEFAULT 0,
            session_metadata JSON,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            started_at TIMESTAMP WITH TIME ZONE,
            completed_at TIMESTAMP WITH TIME ZONE,
            total_phases INTEGER
        );
        RAISE NOTICE 'Created manga_sessions table';
    ELSE
        RAISE NOTICE 'manga_sessions table already exists';

        -- Ensure critical columns exist in manga_sessions
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'manga_sessions' AND column_name = 'request_id'
        ) THEN
            ALTER TABLE manga_sessions ADD COLUMN request_id UUID UNIQUE DEFAULT uuid_generate_v4();
            UPDATE manga_sessions SET request_id = uuid_generate_v4() WHERE request_id IS NULL;
            RAISE NOTICE 'Added request_id column to manga_sessions';
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'manga_sessions' AND column_name = 'session_metadata'
        ) THEN
            ALTER TABLE manga_sessions ADD COLUMN session_metadata JSON;
            RAISE NOTICE 'Added session_metadata column to manga_sessions';
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'manga_sessions' AND column_name = 'current_phase'
        ) THEN
            ALTER TABLE manga_sessions ADD COLUMN current_phase INTEGER;
            RAISE NOTICE 'Added current_phase column to manga_sessions';
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'manga_sessions' AND column_name = 'total_phases'
        ) THEN
            ALTER TABLE manga_sessions ADD COLUMN total_phases INTEGER;
            RAISE NOTICE 'Added total_phases column to manga_sessions';
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'manga_sessions' AND column_name = 'project_id'
        ) THEN
            ALTER TABLE manga_sessions ADD COLUMN project_id UUID;
            RAISE NOTICE 'Added project_id column to manga_sessions';
        END IF;
    END IF;

    -- Create session_messages table (CRITICAL MISSING TABLE)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'session_messages'
    ) THEN
        CREATE TABLE session_messages (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            session_id UUID NOT NULL REFERENCES manga_sessions(id) ON DELETE CASCADE,
            message_type VARCHAR(20) NOT NULL,
            content TEXT NOT NULL,
            phase INTEGER,
            message_metadata JSON DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
        RAISE NOTICE 'Created session_messages table';
    ELSE
        RAISE NOTICE 'session_messages table already exists';
    END IF;

    -- Create session_events table (ADDITIONAL MISSING TABLE)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'session_events'
    ) THEN
        CREATE TABLE session_events (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            session_id UUID NOT NULL REFERENCES manga_sessions(id) ON DELETE CASCADE,
            event_type VARCHAR(50) NOT NULL,
            event_data JSON NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
        RAISE NOTICE 'Created session_events table';
    ELSE
        RAISE NOTICE 'session_events table already exists';
    END IF;

    -- Create preview_versions table if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'preview_versions'
    ) THEN
        CREATE TABLE preview_versions (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            session_id UUID NOT NULL REFERENCES manga_sessions(id) ON DELETE CASCADE,
            phase INTEGER NOT NULL,
            parent_version_id UUID REFERENCES preview_versions(id) ON DELETE SET NULL,
            version_data JSON,
            change_description VARCHAR(255),
            quality_level INTEGER,
            quality_score NUMERIC(4,2),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
        RAISE NOTICE 'Created preview_versions table';
    ELSE
        RAISE NOTICE 'preview_versions table already exists';
    END IF;

    -- Create phase_results table if not exists (PREVIOUSLY FIXED)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'phase_results'
    ) THEN
        CREATE TABLE phase_results (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            session_id UUID NOT NULL REFERENCES manga_sessions(id) ON DELETE CASCADE,
            phase INTEGER NOT NULL,
            status VARCHAR(32) NOT NULL DEFAULT 'pending',
            content JSON,
            quality_score NUMERIC(4,2),
            preview_version_id UUID REFERENCES preview_versions(id) ON DELETE SET NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
        RAISE NOTICE 'Created phase_results table';
    ELSE
        RAISE NOTICE 'phase_results table already exists';

        -- Ensure the critical 'phase' column exists
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'phase_results' AND column_name = 'phase'
        ) THEN
            ALTER TABLE phase_results ADD COLUMN phase INTEGER NOT NULL DEFAULT 1;
            RAISE NOTICE 'Added phase column to phase_results table';
        END IF;
    END IF;

    -- Create preview_cache_metadata table if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'preview_cache_metadata'
    ) THEN
        CREATE TABLE preview_cache_metadata (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            cache_key VARCHAR(255) NOT NULL UNIQUE,
            version_id UUID NOT NULL REFERENCES preview_versions(id) ON DELETE CASCADE,
            phase INTEGER NOT NULL,
            quality_level INTEGER NOT NULL,
            signed_url VARCHAR(2048) NOT NULL,
            content_type VARCHAR(100) NOT NULL DEFAULT 'application/json',
            file_size NUMERIC(12,0),
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            last_accessed TIMESTAMP WITH TIME ZONE
        );
        RAISE NOTICE 'Created preview_cache_metadata table';
    ELSE
        RAISE NOTICE 'preview_cache_metadata table already exists';
    END IF;

    -- Create user_feedback table if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'user_feedback'
    ) THEN
        CREATE TABLE user_feedback (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            session_id UUID NOT NULL REFERENCES manga_sessions(id) ON DELETE CASCADE,
            phase INTEGER NOT NULL,
            feedback_type VARCHAR(32) NOT NULL DEFAULT 'natural_language',
            payload JSON NOT NULL,
            sentiment_score NUMERIC(4,2),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
        RAISE NOTICE 'Created user_feedback table';
    ELSE
        RAISE NOTICE 'user_feedback table already exists';
    END IF;

    -- Create generated_images table if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'generated_images'
    ) THEN
        CREATE TABLE generated_images (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            session_id UUID NOT NULL REFERENCES manga_sessions(id) ON DELETE CASCADE,
            phase INTEGER NOT NULL,
            storage_path VARCHAR(512) NOT NULL,
            signed_url VARCHAR(2048),
            image_metadata JSON,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
        RAISE NOTICE 'Created generated_images table';
    ELSE
        RAISE NOTICE 'generated_images table already exists';
    END IF;

    -- Create indices if they don't exist
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'phase_results' AND indexname = 'ix_phase_results_session_phase'
    ) THEN
        CREATE INDEX ix_phase_results_session_phase ON phase_results(session_id, phase);
        RAISE NOTICE 'Created index ix_phase_results_session_phase';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'preview_versions' AND indexname = 'ix_preview_versions_session_phase'
    ) THEN
        CREATE INDEX ix_preview_versions_session_phase ON preview_versions(session_id, phase);
        RAISE NOTICE 'Created index ix_preview_versions_session_phase';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'user_feedback' AND indexname = 'ix_user_feedback_session_phase'
    ) THEN
        CREATE INDEX ix_user_feedback_session_phase ON user_feedback(session_id, phase);
        RAISE NOTICE 'Created index ix_user_feedback_session_phase';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'session_messages' AND indexname = 'ix_session_messages_session_id'
    ) THEN
        CREATE INDEX ix_session_messages_session_id ON session_messages(session_id);
        RAISE NOTICE 'Created index ix_session_messages_session_id';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'session_events' AND indexname = 'ix_session_events_session_id'
    ) THEN
        CREATE INDEX ix_session_events_session_id ON session_events(session_id);
        RAISE NOTICE 'Created index ix_session_events_session_id';
    END IF;

    -- Mark migration as complete by creating/updating alembic_version table
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'alembic_version'
    ) THEN
        CREATE TABLE alembic_version (
            version_num VARCHAR(32) NOT NULL PRIMARY KEY
        );
        INSERT INTO alembic_version (version_num) VALUES ('0009_ensure_request_id_exists');
        RAISE NOTICE 'Created alembic_version table with current version';
    ELSE
        UPDATE alembic_version SET version_num = '0009_ensure_request_id_exists';
        RAISE NOTICE 'Updated alembic_version to current version';
    END IF;

    RAISE NOTICE 'Complete schema fix v2 completed successfully!';
END $$;

-- Verify all critical tables and columns exist
SELECT 'Complete Schema Verification Results:' as message;

SELECT
    t.table_name,
    CASE
        WHEN t.table_name = 'manga_sessions' THEN 'Core session management'
        WHEN t.table_name = 'phase_results' THEN 'Pipeline execution results'
        WHEN t.table_name = 'session_messages' THEN 'CRITICAL - Session messaging'
        WHEN t.table_name = 'session_events' THEN 'CRITICAL - Session events'
        WHEN t.table_name = 'preview_versions' THEN 'Preview generation'
        WHEN t.table_name = 'user_feedback' THEN 'User interaction'
        WHEN t.table_name = 'generated_images' THEN 'Image storage'
        WHEN t.table_name = 'preview_cache_metadata' THEN 'Cache management'
        ELSE 'Other'
    END as purpose
FROM information_schema.tables t
WHERE t.table_schema = 'public'
AND t.table_name IN ('manga_sessions', 'phase_results', 'session_messages', 'session_events', 'preview_versions', 'user_feedback', 'generated_images', 'preview_cache_metadata')
ORDER BY t.table_name;

-- Specifically verify session_messages table structure
SELECT
    'session_messages verification:' as check_type,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'session_messages'
ORDER BY ordinal_position;

-- Specifically verify session_events table structure
SELECT
    'session_events verification:' as check_type,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'session_events'
ORDER BY ordinal_position;