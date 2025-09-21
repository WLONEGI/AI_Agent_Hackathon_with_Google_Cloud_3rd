-- Fix missing request_id column in manga_sessions table
-- This adds the request_id column if it doesn't exist

-- Check if request_id column exists, if not add it
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'manga_sessions'
        AND column_name = 'request_id'
    ) THEN
        -- Add the request_id column
        ALTER TABLE manga_sessions
        ADD COLUMN request_id UUID UNIQUE DEFAULT gen_random_uuid();

        -- Update existing records to have request_id values
        UPDATE manga_sessions
        SET request_id = gen_random_uuid()
        WHERE request_id IS NULL;

        RAISE NOTICE 'Added request_id column to manga_sessions table';
    ELSE
        RAISE NOTICE 'request_id column already exists in manga_sessions table';
    END IF;
END $$;

-- Make sure we have all necessary columns
DO $$
BEGIN
    -- Check if other columns exist and add them if missing
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'manga_sessions'
        AND column_name = 'session_metadata'
    ) THEN
        ALTER TABLE manga_sessions
        ADD COLUMN session_metadata JSON;
        RAISE NOTICE 'Added session_metadata column';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'manga_sessions'
        AND column_name = 'current_phase'
    ) THEN
        ALTER TABLE manga_sessions
        ADD COLUMN current_phase INTEGER DEFAULT 0;
        RAISE NOTICE 'Added current_phase column';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'manga_sessions'
        AND column_name = 'total_phases'
    ) THEN
        ALTER TABLE manga_sessions
        ADD COLUMN total_phases INTEGER DEFAULT 5;
        RAISE NOTICE 'Added total_phases column';
    END IF;
END $$;