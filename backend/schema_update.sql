-- Adding firebase_uid column to users table
DO $$
BEGIN
    -- Add firebase_uid column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'firebase_uid'
    ) THEN
        ALTER TABLE users ADD COLUMN firebase_uid VARCHAR(128);
        RAISE NOTICE 'Added firebase_uid column';
    END IF;
    
    -- Add unique constraint if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'users_firebase_uid_key' AND table_name = 'users'
    ) THEN
        ALTER TABLE users ADD CONSTRAINT users_firebase_uid_key UNIQUE (firebase_uid);
        RAISE NOTICE 'Added unique constraint on firebase_uid';
    END IF;
    
    -- Update NULL values
    UPDATE users SET firebase_uid = 'temp_uid_' || id::text || '_' || extract(epoch from now())::text
    WHERE firebase_uid IS NULL;
    
    -- Make column NOT NULL
    ALTER TABLE users ALTER COLUMN firebase_uid SET NOT NULL;
    
    RAISE NOTICE 'firebase_uid column setup completed';
END $$;
