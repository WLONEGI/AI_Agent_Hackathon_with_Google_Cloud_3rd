#!/usr/bin/env python3
"""
手動SQLでusersテーブルを作成するスクリプト
"""
import asyncio
import asyncpg
import os
from app.core.settings import get_settings

async def create_users_tables():
    """usersテーブルとuser_refresh_tokensテーブルを手動作成"""
    try:
        settings = get_settings()
        database_url = str(settings.database_url)
        print(f'データベース接続: {database_url[:50]}...')

        conn = await asyncpg.connect(database_url)

        print("=== 手動でusersテーブル作成開始 ===")

        # usersテーブル作成
        await conn.execute("""
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
        """)
        print("✅ usersテーブル作成完了")

        # user_refresh_tokensテーブル作成
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_refresh_tokens (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                token_hash VARCHAR(64) NOT NULL UNIQUE,
                expires_at TIMESTAMP NOT NULL,
                revoked_at TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            );
        """)
        print("✅ user_refresh_tokensテーブル作成完了")

        # インデックス作成
        await conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_firebase_uid ON users (firebase_uid);")
        await conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email);")
        await conn.execute("CREATE INDEX IF NOT EXISTS ix_user_refresh_tokens_user_id ON user_refresh_tokens (user_id);")
        await conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_user_refresh_tokens_token_hash ON user_refresh_tokens (token_hash);")
        print("✅ インデックス作成完了")

        # alembic_versionテーブル更新
        try:
            await conn.execute("INSERT INTO alembic_version (version_num) VALUES ('0006_add_user_tables') ON CONFLICT (version_num) DO NOTHING;")
            print("✅ alembic_version更新完了")
        except Exception as e:
            print(f"⚠️ alembic_version更新スキップ: {e}")

        # 確認用: テーブル構造表示
        tables = await conn.fetch("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name IN ('users', 'user_refresh_tokens')
            ORDER BY table_name;
        """)

        print("\\n=== 作成されたテーブル確認 ===")
        for table in tables:
            print(f"  ✅ {table['table_name']}")

        # usersテーブル構造確認
        columns = await conn.fetch("""
            SELECT column_name, data_type FROM information_schema.columns
            WHERE table_name = 'users' AND table_schema = 'public'
            ORDER BY ordinal_position;
        """)

        print("\\n=== usersテーブル構造確認 ===")
        for col in columns:
            print(f"  - {col['column_name']}: {col['data_type']}")

        await conn.close()
        print("\\n🎉 手動テーブル作成完了! 認証システムが動作するはずです。")
        return True

    except Exception as e:
        print(f"❌ 手動テーブル作成エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(create_users_tables())
    exit(0 if success else 1)