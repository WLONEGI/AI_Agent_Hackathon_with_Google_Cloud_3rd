#!/usr/bin/env python3
"""
マイグレーション実行スクリプト
Cloud Runジョブとして実行されることを想定
"""
import os
import sys
from alembic.config import Config
from alembic import command
from app.core.settings import get_settings

def run_migration():
    """Alembicマイグレーションを実行"""
    try:
        # 設定を取得
        settings = get_settings()

        # Alembic設定
        alembic_cfg = Config("alembic.ini")

        # データベースURLを設定から取得
        database_url = str(settings.database_url)
        # asyncpgをpsycopg2に変更（Alembicはsyncドライバーを使用）
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
        alembic_cfg.set_main_option("sqlalchemy.url", database_url)

        print("マイグレーション開始...")
        print(f"データベースURL: {database_url}")

        # マイグレーション実行
        command.upgrade(alembic_cfg, "head")

        print("マイグレーション完了!")
        return True

    except Exception as e:
        print(f"マイグレーションエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)