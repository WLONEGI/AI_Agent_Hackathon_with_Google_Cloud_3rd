#!/usr/bin/env python3
"""
マイグレーション実行スクリプト
Cloud Runジョブとして実行されることを想定
"""
import os
import sys
import asyncio
import asyncpg
from alembic.config import Config
from alembic import command
from app.core.settings import get_settings

async def test_database_connection(database_url: str) -> bool:
    """データベース接続テスト"""
    try:
        # asyncpgで直接接続テスト
        conn = await asyncpg.connect(database_url)

        # 既存テーブルの確認
        tables = await conn.fetch("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)

        print("=== 既存テーブル一覧 ===")
        for table in tables:
            print(f"  - {table['table_name']}")

        # usersテーブルが存在するかチェック
        users_table = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'users' AND table_schema = 'public'
            ORDER BY ordinal_position;
        """)

        if users_table:
            print("\n=== usersテーブル構造 ===")
            for col in users_table:
                print(f"  - {col['column_name']}: {col['data_type']} (NULL: {col['is_nullable']})")
        else:
            print("\n=== usersテーブルは存在しません - 手動作成を開始 ===")

            # usersテーブル手動作成
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

            print("🎉 手動テーブル作成完了!")

        # Alembicバージョンテーブルの確認
        try:
            version = await conn.fetchrow("SELECT version_num FROM alembic_version;")
            if version:
                print(f"\n=== 現在のAlembicバージョン: {version['version_num']} ===")
            else:
                print("\n=== Alembicバージョンテーブルは空です ===")
        except:
            print("\n=== Alembicバージョンテーブルが存在しません ===")

        await conn.close()
        return True

    except Exception as e:
        print(f"データベース接続エラー: {e}")
        return False

def run_migration():
    """Alembicマイグレーションを実行"""
    try:
        print("=== マイグレーション実行開始 ===")

        # 設定を取得
        settings = get_settings()
        print(f"APP_ENV: {settings.app_env}")

        # データベースURLを設定から取得
        database_url = str(settings.database_url)
        print(f"元のデータベースURL: {database_url[:50]}...")

        # asyncpg用のURLでデータベース接続テスト
        print("\n=== データベース接続テスト ===")
        connection_success = asyncio.run(test_database_connection(database_url))

        if not connection_success:
            print("データベース接続に失敗しました")
            return False

        # Alembic用にsyncドライバーに変更
        sync_database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
        print(f"Alembic用URL: {sync_database_url[:50]}...")

        # Alembic設定
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", sync_database_url)

        print("\n=== 現在のマイグレーション状況確認 ===")
        try:
            command.current(alembic_cfg)
        except Exception as e:
            print(f"現在のバージョン取得エラー: {e}")

        print("\n=== 利用可能なマイグレーション確認 ===")
        try:
            command.history(alembic_cfg)
        except Exception as e:
            print(f"履歴取得エラー: {e}")

        print("\n=== マイグレーション実行 ===")
        command.upgrade(alembic_cfg, "head")

        print("\n=== マイグレーション実行後の状況確認 ===")
        # 再度データベース状態を確認
        asyncio.run(test_database_connection(database_url))

        print("\n=== マイグレーション完了! ===")
        return True

    except Exception as e:
        print(f"\n=== マイグレーションエラー ===")
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)