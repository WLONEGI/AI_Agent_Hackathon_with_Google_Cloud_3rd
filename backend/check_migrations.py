#!/usr/bin/env python3
"""
Check current migration status and apply missing HITL migrations
"""

import os
import asyncio
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Database connection parameters
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5433,
    'user': 'manga_user',
    'password': 'manga_secure_password_2024',
    'database': 'manga_db'
}

async def check_migration_status():
    """Check current Alembic migration status"""

    print("🔍 データベース接続確認...")

    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Check if alembic_version table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'alembic_version'
            );
        """)
        alembic_exists = cursor.fetchone()[0]

        if not alembic_exists:
            print("❌ alembic_version テーブルが存在しません")
            return None

        # Get current version
        cursor.execute("SELECT version_num FROM alembic_version;")
        current_version = cursor.fetchone()

        if current_version:
            current_version = current_version[0]
            print(f"✅ 現在のマイグレーションバージョン: {current_version}")
        else:
            print("⚠️ マイグレーションバージョンが設定されていません")
            current_version = None

        # Check if HITL tables exist
        hitl_tables = ['phase_feedback_states', 'user_feedback_history', 'feedback_option_templates']

        print("🔍 HITLテーブル存在確認...")
        for table in hitl_tables:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = %s
                );
            """, (table,))
            exists = cursor.fetchone()[0]
            status = "✅ 存在" if exists else "❌ 不在"
            print(f"  {table}: {status}")

        # Check manga_sessions for HITL columns
        print("🔍 manga_sessions HITLカラム確認...")
        hitl_columns = ['waiting_for_feedback', 'feedback_timeout_at', 'total_feedback_count', 'hitl_enabled']

        for column in hitl_columns:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_name = 'manga_sessions' AND column_name = %s
                );
            """, (column,))
            exists = cursor.fetchone()[0]
            status = "✅ 存在" if exists else "❌ 不在"
            print(f"  {column}: {status}")

        cursor.close()
        conn.close()

        return current_version

    except Exception as e:
        print(f"❌ データベース接続エラー: {e}")
        return None

async def run_specific_migration():
    """Run specific migration using alembic"""

    print("🚀 Alembicマイグレーション実行...")

    # Set environment variables
    os.environ['DATABASE_URL'] = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

    # Run alembic upgrade to specific version
    import subprocess

    try:
        # Run alembic current to check status
        print("📋 現在のマイグレーション状況:")
        result = subprocess.run(['alembic', 'current'], capture_output=True, text=True, cwd='/Users/negishi/develop/AI_Agent_Hackathon_with_Google_Cloud_3rd/backend')
        print(result.stdout)
        if result.stderr:
            print(f"⚠️ stderr: {result.stderr}")

        # Run alembic history to see available migrations
        print("📚 利用可能なマイグレーション:")
        result = subprocess.run(['alembic', 'history'], capture_output=True, text=True, cwd='/Users/negishi/develop/AI_Agent_Hackathon_with_Google_Cloud_3rd/backend')
        print(result.stdout)
        if result.stderr:
            print(f"⚠️ stderr: {result.stderr}")

        # Upgrade to head (latest)
        print("🔄 最新マイグレーションを適用中...")
        result = subprocess.run(['alembic', 'upgrade', 'head'], capture_output=True, text=True, cwd='/Users/negishi/develop/AI_Agent_Hackathon_with_Google_Cloud_3rd/backend')
        print(result.stdout)

        if result.returncode == 0:
            print("✅ マイグレーション適用成功！")
            return True
        else:
            print(f"❌ マイグレーション適用失敗: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ マイグレーション実行エラー: {e}")
        return False

async def main():
    """Main execution"""

    print("🎯 === HITL マイグレーション修正スクリプト ===")

    # Check current status
    current_version = await check_migration_status()

    if current_version != "0007_add_hitl_tables":
        print("📦 HITLマイグレーションが未適用です。適用を開始します...")
        success = await run_specific_migration()

        if success:
            print("🔍 適用後の状況を再確認...")
            await check_migration_status()
        else:
            print("❌ マイグレーション適用に失敗しました")
    else:
        print("✅ HITLマイグレーションは既に適用済みです")

if __name__ == "__main__":
    asyncio.run(main())