#!/usr/bin/env python3
"""
データベーステーブル存在確認スクリプト
"""
import asyncio
import asyncpg
import os
from app.core.settings import get_settings

async def verify_database_tables():
    """データベーステーブルの存在と構造を確認"""
    try:
        settings = get_settings()
        database_url = str(settings.database_url)
        print(f'データベース接続: {database_url[:50]}...')

        conn = await asyncpg.connect(database_url)

        # 全テーブル一覧
        tables = await conn.fetch("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)

        print("\n=== 全テーブル一覧 ===")
        for table in tables:
            print(f"  ✅ {table['table_name']}")

        # usersテーブル詳細
        users_columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'users' AND table_schema = 'public'
            ORDER BY ordinal_position;
        """)

        if users_columns:
            print("\n=== usersテーブル構造 ===")
            for col in users_columns:
                print(f"  - {col['column_name']}: {col['data_type']} (NULL: {col['is_nullable']}) DEFAULT: {col['column_default']}")
        else:
            print("\n❌ usersテーブルが存在しません")

        # user_refresh_tokensテーブル詳細
        refresh_tokens_columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'user_refresh_tokens' AND table_schema = 'public'
            ORDER BY ordinal_position;
        """)

        if refresh_tokens_columns:
            print("\n=== user_refresh_tokensテーブル構造 ===")
            for col in refresh_tokens_columns:
                print(f"  - {col['column_name']}: {col['data_type']} (NULL: {col['is_nullable']})")
        else:
            print("\n❌ user_refresh_tokensテーブルが存在しません")

        # インデックス確認
        indexes = await conn.fetch("""
            SELECT indexname, tablename, indexdef
            FROM pg_indexes
            WHERE tablename IN ('users', 'user_refresh_tokens')
            ORDER BY tablename, indexname;
        """)

        print("\n=== インデックス一覧 ===")
        for idx in indexes:
            print(f"  - {idx['indexname']} on {idx['tablename']}")

        # alembic_versionテーブル確認
        try:
            version = await conn.fetchrow("SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 1;")
            if version:
                print(f"\n=== 現在のAlembicバージョン: {version['version_num']} ===")
            else:
                print("\n=== Alembicバージョンテーブルは空です ===")
        except Exception as e:
            print(f"\n⚠️ Alembicバージョンテーブルアクセスエラー: {e}")

        # テスト用クエリ実行
        try:
            test_query = "SELECT firebase_uid FROM users LIMIT 1;"
            await conn.fetch(test_query)
            print(f"\n✅ テストクエリ成功: {test_query}")
        except Exception as e:
            print(f"\n❌ テストクエリ失敗: {e}")

        await conn.close()
        print("\n🎉 データベース確認完了!")
        return True

    except Exception as e:
        print(f"❌ データベース確認エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(verify_database_tables())
    exit(0 if success else 1)