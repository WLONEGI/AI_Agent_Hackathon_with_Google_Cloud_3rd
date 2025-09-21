-- Schema fix for manga_sessions table
-- Add request_id column if it doesn't exist

ALTER TABLE manga_sessions ADD COLUMN IF NOT EXISTS request_id UUID;
ALTER TABLE manga_sessions ADD COLUMN IF NOT EXISTS project_id UUID;
ALTER TABLE manga_sessions ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0;
ALTER TABLE manga_sessions ADD COLUMN IF NOT EXISTS session_metadata JSON;
ALTER TABLE manga_sessions ADD COLUMN IF NOT EXISTS text TEXT;
ALTER TABLE manga_sessions ADD COLUMN IF NOT EXISTS ai_auto_settings BOOLEAN DEFAULT TRUE;
ALTER TABLE manga_sessions ADD COLUMN IF NOT EXISTS feedback_mode JSON;
ALTER TABLE manga_sessions ADD COLUMN IF NOT EXISTS options JSON;
ALTER TABLE manga_sessions ADD COLUMN IF NOT EXISTS estimated_completion_time TIMESTAMP WITH TIME ZONE;
ALTER TABLE manga_sessions ADD COLUMN IF NOT EXISTS actual_completion_time TIMESTAMP WITH TIME ZONE;
ALTER TABLE manga_sessions ADD COLUMN IF NOT EXISTS total_phases INTEGER DEFAULT 5;
ALTER TABLE manga_sessions ADD COLUMN IF NOT EXISTS error_message TEXT;
ALTER TABLE manga_sessions ADD COLUMN IF NOT EXISTS websocket_channel VARCHAR(255);

-- Generate request_id for existing records
UPDATE manga_sessions SET request_id = gen_random_uuid() WHERE request_id IS NULL;

-- Add unique constraint if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'uq_manga_sessions_request_id'
        AND table_name = 'manga_sessions'
    ) THEN
        ALTER TABLE manga_sessions ADD CONSTRAINT uq_manga_sessions_request_id UNIQUE (request_id);
    END IF;
END$$;