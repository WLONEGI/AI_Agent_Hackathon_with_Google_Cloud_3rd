-- Add missing request_id column to manga_sessions
-- This is essential for the pipeline service to work

DO $$
BEGIN
    -- Check and add request_id column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'manga_sessions' AND column_name = 'request_id') THEN

        -- Add the request_id column
        ALTER TABLE manga_sessions ADD COLUMN request_id UUID UNIQUE;

        -- Generate request_id for existing records that don't have one
        UPDATE manga_sessions
        SET request_id = gen_random_uuid()
        WHERE request_id IS NULL;

        -- Make request_id NOT NULL after populating existing records
        ALTER TABLE manga_sessions ALTER COLUMN request_id SET NOT NULL;

        -- Create index for performance
        CREATE INDEX IF NOT EXISTS ix_manga_sessions_request_id ON manga_sessions(request_id);

        RAISE NOTICE '✅ request_id column added to manga_sessions table';
    ELSE
        RAISE NOTICE '⚠️ request_id column already exists in manga_sessions table';
    END IF;

    -- Update alembic version to reflect that this part of 0008 was applied
    UPDATE alembic_version SET version_num = '0008_unify_manga_session_schema'
    WHERE version_num = '0007_add_hitl_tables';

    -- If alembic version was not 0007, still update it
    INSERT INTO alembic_version (version_num) VALUES ('0008_unify_manga_session_schema')
    ON CONFLICT (version_num) DO NOTHING;

END $$;

-- Verify the column was added
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'manga_sessions' AND column_name = 'request_id') THEN
        RAISE NOTICE '🎯 SUCCESS: request_id column is now available in manga_sessions';
    ELSE
        RAISE NOTICE '❌ FAILED: request_id column was not added to manga_sessions';
    END IF;
END $$;