-- Add firebase_uid column to users table
-- This column is required for Firebase authentication integration

-- Check if the column already exists, if not add it
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users'
        AND column_name = 'firebase_uid'
    ) THEN
        -- Add the firebase_uid column
        ALTER TABLE users ADD COLUMN firebase_uid VARCHAR(128);

        -- Add unique constraint
        ALTER TABLE users ADD CONSTRAINT users_firebase_uid_key UNIQUE (firebase_uid);

        -- Create index for performance
        CREATE UNIQUE INDEX ix_users_firebase_uid ON users(firebase_uid);

        -- Update existing rows with temporary values (if any exist)
        UPDATE users SET firebase_uid = 'temp_uid_' || id::text || '_' || extract(epoch from now())::text
        WHERE firebase_uid IS NULL;

        -- Make the column NOT NULL after updating existing rows
        ALTER TABLE users ALTER COLUMN firebase_uid SET NOT NULL;

        RAISE NOTICE 'firebase_uid column added successfully to users table';
    ELSE
        RAISE NOTICE 'firebase_uid column already exists in users table';
    END IF;
END $$;

-- Verify the schema change
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'users' AND column_name = 'firebase_uid';