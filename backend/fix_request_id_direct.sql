-- Add request_id column to manga_sessions via gcloud sql query
ALTER TABLE manga_sessions ADD COLUMN IF NOT EXISTS request_id UUID;

-- Generate UUIDs for existing records
UPDATE manga_sessions
SET request_id = gen_random_uuid()
WHERE request_id IS NULL;

-- Create unique index
CREATE UNIQUE INDEX IF NOT EXISTS ix_manga_sessions_request_id ON manga_sessions(request_id);

-- Update alembic version
UPDATE alembic_version SET version_num = '0008_unify_manga_session_schema';