#!/usr/bin/env python3
"""
データベース初期化スクリプト
"""
import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Set environment variables
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///./manga_service.db'

async def main():
    """データベース初期化実行"""
    print("🗄️  データベース初期化開始...")
    
    try:
        from app.core.database import init_db
        from app.models import user, manga, quality_gates  # Import all models to register them
        
        await init_db()
        print("✅ データベーステーブル作成完了")
        
    except Exception as e:
        print(f"❌ データベース初期化エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("🎉 データベース初期化が正常に完了しました!")
    else:
        print("💥 データベース初期化に失敗しました。")
        sys.exit(1)