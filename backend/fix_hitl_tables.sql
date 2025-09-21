-- Fix missing HITL tables based on 0007_add_hitl_tables migration
-- This script creates the missing tables that are causing HTTP 500 errors

-- Create user_feedback_history table
CREATE TABLE IF NOT EXISTS user_feedback_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES manga_sessions(id) ON DELETE CASCADE,
    phase INTEGER NOT NULL,
    feedback_type VARCHAR(50) NOT NULL, -- approval, modification, skip
    feedback_data JSON,
    user_satisfaction_score FLOAT,
    natural_language_input TEXT,
    selected_options TEXT[],
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    processing_completed_at TIMESTAMP WITH TIME ZONE
);

-- Create phase_feedback_states table
CREATE TABLE IF NOT EXISTS phase_feedback_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES manga_sessions(id) ON DELETE CASCADE,
    phase INTEGER NOT NULL,
    state VARCHAR(50) NOT NULL, -- waiting, received, processing, completed, timeout
    preview_data JSON,
    feedback_started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    feedback_timeout_at TIMESTAMP WITH TIME ZONE,
    feedback_received_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(session_id, phase)
);

-- Create feedback_option_templates table
CREATE TABLE IF NOT EXISTS feedback_option_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phase INTEGER NOT NULL,
    option_key VARCHAR(100) NOT NULL,
    option_label TEXT NOT NULL,
    option_description TEXT,
    option_category VARCHAR(50),
    is_active BOOLEAN NOT NULL DEFAULT true,
    display_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(phase, option_key)
);

-- Add missing columns to manga_sessions if they don't exist
DO $$
BEGIN
    -- Check and add waiting_for_feedback column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'manga_sessions' AND column_name = 'waiting_for_feedback') THEN
        ALTER TABLE manga_sessions ADD COLUMN waiting_for_feedback BOOLEAN NOT NULL DEFAULT false;
    END IF;

    -- Check and add feedback_timeout_at column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'manga_sessions' AND column_name = 'feedback_timeout_at') THEN
        ALTER TABLE manga_sessions ADD COLUMN feedback_timeout_at TIMESTAMP WITH TIME ZONE;
    END IF;

    -- Check and add total_feedback_count column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'manga_sessions' AND column_name = 'total_feedback_count') THEN
        ALTER TABLE manga_sessions ADD COLUMN total_feedback_count INTEGER NOT NULL DEFAULT 0;
    END IF;

    -- Check and add hitl_enabled column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'manga_sessions' AND column_name = 'hitl_enabled') THEN
        ALTER TABLE manga_sessions ADD COLUMN hitl_enabled BOOLEAN NOT NULL DEFAULT false;
    END IF;
END $$;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS ix_user_feedback_history_session_id ON user_feedback_history(session_id);
CREATE INDEX IF NOT EXISTS ix_user_feedback_history_phase ON user_feedback_history(phase);
CREATE INDEX IF NOT EXISTS ix_user_feedback_history_created_at ON user_feedback_history(created_at);

CREATE INDEX IF NOT EXISTS ix_phase_feedback_states_session_id ON phase_feedback_states(session_id);
CREATE INDEX IF NOT EXISTS ix_phase_feedback_states_state ON phase_feedback_states(state);
CREATE INDEX IF NOT EXISTS ix_phase_feedback_states_timeout ON phase_feedback_states(feedback_timeout_at);

CREATE INDEX IF NOT EXISTS ix_feedback_option_templates_phase ON feedback_option_templates(phase);
CREATE INDEX IF NOT EXISTS ix_feedback_option_templates_active ON feedback_option_templates(is_active);

-- Update alembic_version to reflect 0007 migration as applied
INSERT INTO alembic_version (version_num) VALUES ('0007_add_hitl_tables')
ON CONFLICT (version_num) DO NOTHING;

-- Update version if it was different
UPDATE alembic_version SET version_num = '0007_add_hitl_tables'
WHERE version_num != '0007_add_hitl_tables';

-- Verify tables were created
DO $$
BEGIN
    RAISE NOTICE '=== HITL Tables Creation Complete ===';

    -- Check if tables exist
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'phase_feedback_states') THEN
        RAISE NOTICE '✅ phase_feedback_states table created successfully';
    ELSE
        RAISE NOTICE '❌ phase_feedback_states table creation failed';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_feedback_history') THEN
        RAISE NOTICE '✅ user_feedback_history table created successfully';
    ELSE
        RAISE NOTICE '❌ user_feedback_history table creation failed';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'feedback_option_templates') THEN
        RAISE NOTICE '✅ feedback_option_templates table created successfully';
    ELSE
        RAISE NOTICE '❌ feedback_option_templates table creation failed';
    END IF;
END $$;