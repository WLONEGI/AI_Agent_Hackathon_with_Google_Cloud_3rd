# 設計書外エンドポイント整理分析

## 🎯 削除対象の判断

### ✅ **削除実行: engine.py**
**根拠:**
- main.pyのapi_routerに含まれていない（実際に使用されていない）
- manga_sessions.pyと機能完全重複
- POST /generateのURL衝突原因
- 設計書外の独自実装

### ⚠️ **保持推奨: quality_gates.py**
**根拠:**
- api_routerに意図的に含まれている
- main.pyのfeaturesで "quality_gates": True として宣言
- 設計書外だが有用な拡張機能として実装
- 実際の運用では品質管理は重要

### ⚠️ **保持推奨: preview_interactive.py**
**根拠:**
- api_routerに意図的に含まれている  
- main.pyのfeaturesで "preview_interactive": True として宣言
- HITLフィードバックシステムの重要な拡張機能
- ユーザビリティ向上に貢献

## 🔧 実行アクション
1. engine.py削除（URL衝突解決）
2. quality_gates.py, preview_interactive.pyは設計書外だが価値ある拡張機能として保持
3. 最終的な設計書準拠性レポート更新