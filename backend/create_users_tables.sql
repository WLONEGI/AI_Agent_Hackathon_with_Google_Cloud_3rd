-- 手動でusersテーブルとuser_refresh_tokensテーブルを作成
-- マイグレーション0006_add_user_tables.pyと同じ構造

-- usersテーブル作成
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    firebase_uid VARCHAR(128) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255),
    account_type VARCHAR(32) NOT NULL DEFAULT 'free',
    is_active BOOLEAN NOT NULL DEFAULT true,
    firebase_claims JSON,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- user_refresh_tokensテーブル作成
CREATE TABLE IF NOT EXISTS user_refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    revoked_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- manga_sessionsテーブルのuser_id外部キー制約追加（テーブルが存在する場合）
DO $$
BEGIN
    -- 外部キー制約が存在しない場合のみ追加
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_manga_sessions_user_id'
    ) THEN
        ALTER TABLE manga_sessions
        ADD CONSTRAINT fk_manga_sessions_user_id
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
    END IF;
EXCEPTION
    WHEN undefined_table THEN
        -- manga_sessionsテーブルが存在しない場合は無視
        RAISE NOTICE 'manga_sessions table does not exist, skipping foreign key constraint';
END $$;

-- インデックス作成
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_firebase_uid ON users (firebase_uid);
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email);
CREATE INDEX IF NOT EXISTS ix_user_refresh_tokens_user_id ON user_refresh_tokens (user_id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_user_refresh_tokens_token_hash ON user_refresh_tokens (token_hash);

-- alembic_versionテーブルを最新バージョンに更新
INSERT INTO alembic_version (version_num) VALUES ('0006_add_user_tables')
ON CONFLICT (version_num) DO NOTHING;