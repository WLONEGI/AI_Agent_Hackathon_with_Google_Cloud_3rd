-- Create missing HITL tables for manga generation system
-- This will complete the schema needed for Human-in-the-Loop functionality

BEGIN;

-- Create user_feedback_history table
CREATE TABLE IF NOT EXISTS user_feedback_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    phase INTEGER NOT NULL,
    feedback_type VARCHAR(50) NOT NULL,
    feedback_data JSONB,
    user_satisfaction_score FLOAT,
    natural_language_input TEXT,
    selected_options TEXT[],
    processing_time_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processing_completed_at TIMESTAMPTZ,
    FOREIGN KEY (session_id) REFERENCES manga_sessions(id) ON DELETE CASCADE
);

-- Create phase_feedback_states table
CREATE TABLE IF NOT EXISTS phase_feedback_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    phase INTEGER NOT NULL,
    state VARCHAR(50) NOT NULL,
    preview_data JSONB,
    feedback_started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    feedback_timeout_at TIMESTAMPTZ,
    feedback_received_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (session_id) REFERENCES manga_sessions(id) ON DELETE CASCADE,
    UNIQUE (session_id, phase)
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
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (phase, option_key)
);

-- Add HITL columns to manga_sessions if they don't exist
DO $$
BEGIN
    -- Add waiting_for_feedback column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'manga_sessions' AND column_name = 'waiting_for_feedback') THEN
        ALTER TABLE manga_sessions ADD COLUMN waiting_for_feedback BOOLEAN NOT NULL DEFAULT false;
    END IF;

    -- Add feedback_timeout_at column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'manga_sessions' AND column_name = 'feedback_timeout_at') THEN
        ALTER TABLE manga_sessions ADD COLUMN feedback_timeout_at TIMESTAMPTZ;
    END IF;

    -- Add total_feedback_count column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'manga_sessions' AND column_name = 'total_feedback_count') THEN
        ALTER TABLE manga_sessions ADD COLUMN total_feedback_count INTEGER NOT NULL DEFAULT 0;
    END IF;

    -- Add hitl_enabled column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'manga_sessions' AND column_name = 'hitl_enabled') THEN
        ALTER TABLE manga_sessions ADD COLUMN hitl_enabled BOOLEAN NOT NULL DEFAULT false;
    END IF;
END $$;

-- Add HITL columns to phase_results if they don't exist
DO $$
BEGIN
    -- Add feedback_integrated column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'phase_results' AND column_name = 'feedback_integrated') THEN
        ALTER TABLE phase_results ADD COLUMN feedback_integrated BOOLEAN NOT NULL DEFAULT false;
    END IF;

    -- Add user_satisfaction_score column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'phase_results' AND column_name = 'user_satisfaction_score') THEN
        ALTER TABLE phase_results ADD COLUMN user_satisfaction_score FLOAT;
    END IF;

    -- Add combined_quality_score column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'phase_results' AND column_name = 'combined_quality_score') THEN
        ALTER TABLE phase_results ADD COLUMN combined_quality_score FLOAT;
    END IF;

    -- Add feedback_summary column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'phase_results' AND column_name = 'feedback_summary') THEN
        ALTER TABLE phase_results ADD COLUMN feedback_summary TEXT;
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

-- Insert default feedback options
INSERT INTO feedback_option_templates (phase, option_key, option_label, option_description, option_category, display_order)
VALUES
    -- Phase 1: Concept Analysis
    (1, 'theme_modify', 'テーマ修正', '物語のテーマを調整したい', 'content', 1),
    (1, 'genre_change', 'ジャンル変更', 'ジャンルを変更したい', 'content', 2),
    (1, 'world_setting_adjust', '世界観調整', '世界設定を修正したい', 'content', 3),
    (1, 'tone_change', '雰囲気変更', '作品の雰囲気を変えたい', 'style', 4),
    (1, 'target_audience_adjust', '対象読者層調整', '想定読者を変更したい', 'content', 5),

    -- Phase 2: Character Design
    (2, 'character_add', 'キャラクター追加', '新しいキャラクターを追加したい', 'content', 1),
    (2, 'character_remove', 'キャラクター削除', 'キャラクターを削除したい', 'content', 2),
    (2, 'personality_change', '性格変更', 'キャラクターの性格を変更したい', 'content', 3),
    (2, 'visual_adjust', 'ビジュアル調整', 'キャラクターの見た目を調整したい', 'style', 4),
    (2, 'relationship_modify', '関係性修正', 'キャラクター同士の関係を修正したい', 'content', 5),

    -- Phase 3: Story Structure
    (3, 'plot_change', 'プロット変更', '物語の展開を変更したい', 'structure', 1),
    (3, 'pacing_adjust', 'ペーシング調整', '物語のテンポを調整したい', 'structure', 2),
    (3, 'climax_modify', 'クライマックス修正', '物語の盛り上がりを修正したい', 'structure', 3),
    (3, 'scene_add', 'シーン追加', '新しいシーンを追加したい', 'content', 4),
    (3, 'scene_remove', 'シーン削除', '不要なシーンを削除したい', 'content', 5)
ON CONFLICT (phase, option_key) DO NOTHING;

-- Update alembic version to indicate HITL tables are now present
UPDATE alembic_version SET version_num = '0007_add_hitl_tables'
WHERE version_num IN ('0006_add_user_tables', '0003_add_refresh_tokens', '0002_create_manga_projects');

-- If no alembic version exists, create it
INSERT INTO alembic_version (version_num) VALUES ('0007_add_hitl_tables')
ON CONFLICT (version_num) DO NOTHING;

COMMIT;

-- Verify tables were created
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'phase_feedback_states') THEN
        RAISE NOTICE '✅ SUCCESS: All HITL tables created successfully';
    ELSE
        RAISE NOTICE '❌ FAILED: HITL tables creation failed';
    END IF;
END $$;