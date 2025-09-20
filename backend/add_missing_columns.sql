-- Add missing columns to users table to match UserAccount model
-- Required columns: display_name, account_type, firebase_claims

DO $$
BEGIN
    -- Add display_name column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users'
        AND column_name = 'display_name'
    ) THEN
        ALTER TABLE users ADD COLUMN display_name VARCHAR(255);
        RAISE NOTICE 'Added display_name column';
    END IF;

    -- Add account_type column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users'
        AND column_name = 'account_type'
    ) THEN
        ALTER TABLE users ADD COLUMN account_type VARCHAR(32) NOT NULL DEFAULT 'free';
        RAISE NOTICE 'Added account_type column';
    END IF;

    -- Add firebase_claims column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users'
        AND column_name = 'firebase_claims'
    ) THEN
        ALTER TABLE users ADD COLUMN firebase_claims JSON;
        RAISE NOTICE 'Added firebase_claims column';
    END IF;

    RAISE NOTICE 'Missing columns setup completed';
END $$;

-- Verify the schema changes
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'users'
AND column_name IN ('display_name', 'account_type', 'firebase_claims')
ORDER BY column_name;