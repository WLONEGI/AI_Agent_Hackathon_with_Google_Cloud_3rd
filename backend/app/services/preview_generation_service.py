"""
PreviewGenerationService - プレビュー生成専用サービス
中間プレビューと最終出力の生成を管理
"""

import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggerMixin
from app.models.manga import PreviewVersion, GeneratedImage


class PreviewGenerationService(LoggerMixin):
    """プレビュー生成専用サービス"""
    
    def __init__(self):
        super().__init__()
    
    async def generate_preview(
        self,
        session_id: str,
        phase_results: List[Dict[str, Any]],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """中間プレビューの生成"""
        try:
            preview_id = f"preview_{session_id}_{int(time.time())}"
            
            # フェーズ結果を統合
            integrated_content = {
                "session_id": session_id,
                "preview_id": preview_id,
                "generated_at": datetime.utcnow().isoformat(),
                "phases": {}
            }
            
            # 各フェーズの結果を統合
            for result in phase_results:
                phase_num = result.get("phase_number")
                if phase_num:
                    integrated_content["phases"][f"phase_{phase_num}"] = {
                        "content": result.get("content", {}),
                        "quality_score": result.get("quality_score"),
                        "metadata": result.get("metadata", {})
                    }
            
            # プレビューバージョンの保存
            preview_version = PreviewVersion(
                id=preview_id,
                session_id=session_id,
                version_number=len(phase_results),
                content=integrated_content,
                quality_score=self._calculate_overall_quality(phase_results),
                created_at=datetime.utcnow()
            )
            
            db.add(preview_version)
            await db.commit()
            
            self.logger.info(f"Preview generated", session_id=session_id, preview_id=preview_id)
            return integrated_content
            
        except Exception as e:
            self.logger.error(f"Preview generation failed: {e}")
            return {"error": str(e)}
    
    async def generate_final_output(
        self,
        session_id: str,
        all_phase_results: List[Dict[str, Any]],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """最終出力の生成"""
        try:
            # 最終統合処理
            final_content = {
                "manga": {
                    "session_id": session_id,
                    "title": self._extract_title(all_phase_results),
                    "pages": self._compile_pages(all_phase_results),
                    "characters": self._extract_characters(all_phase_results),
                    "story_structure": self._extract_story_structure(all_phase_results),
                    "metadata": {
                        "total_phases": len(all_phase_results),
                        "generation_time": self._calculate_total_time(all_phase_results),
                        "overall_quality": self._calculate_overall_quality(all_phase_results),
                        "generated_at": datetime.utcnow().isoformat()
                    }
                }
            }
            
            # 最終バージョンとして保存
            final_preview = PreviewVersion(
                id=f"final_{session_id}",
                session_id=session_id,
                version_number=999,  # 最終版マーカー
                content=final_content,
                quality_score=final_content["manga"]["metadata"]["overall_quality"],
                is_final=True,
                created_at=datetime.utcnow()
            )
            
            db.add(final_preview)
            await db.commit()
            
            self.logger.info(f"Final output generated", session_id=session_id)
            return final_content
            
        except Exception as e:
            self.logger.error(f"Final output generation failed: {e}")
            return {"error": str(e)}
    
    def _calculate_overall_quality(self, phase_results: List[Dict[str, Any]]) -> float:
        """全体的な品質スコアの計算"""
        if not phase_results:
            return 0.0
        
        quality_scores = [
            result.get("quality_score", 0.5)
            for result in phase_results
            if result.get("quality_score") is not None
        ]
        
        if not quality_scores:
            return 0.5
        
        # 重み付き平均（後半フェーズほど重要）
        weights = [1.0, 1.2, 1.4, 1.6, 2.0, 1.5, 1.8]  # フェーズ1-7の重み
        weighted_sum = sum(score * weights[i % len(weights)] for i, score in enumerate(quality_scores))
        weight_sum = sum(weights[:len(quality_scores)])
        
        return weighted_sum / weight_sum if weight_sum > 0 else 0.5
    
    def _extract_title(self, phase_results: List[Dict[str, Any]]) -> str:
        """タイトルの抽出"""
        for result in phase_results:
            if result.get("phase_number") == 1:  # コンセプトフェーズ
                content = result.get("content", {})
                return content.get("title", "無題のマンガ")
        return "無題のマンガ"
    
    def _compile_pages(self, phase_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """ページの統合"""
        pages = []
        
        # フェーズ5（画像）とフェーズ6（セリフ）の結果を統合
        images = {}
        dialogues = {}
        
        for result in phase_results:
            phase_num = result.get("phase_number")
            content = result.get("content", {})
            
            if phase_num == 5:  # 画像フェーズ
                images = content.get("scene_images", {})
            elif phase_num == 6:  # セリフフェーズ
                dialogues = content.get("dialogue_placements", {})
        
        # ページの構築
        max_scenes = max(len(images), len(dialogues))
        for i in range(max_scenes):
            page = {
                "page_number": i + 1,
                "image": images.get(str(i), {}),
                "dialogue": dialogues.get(str(i), {}),
                "layout": "standard"  # デフォルトレイアウト
            }
            pages.append(page)
        
        return pages
    
    def _extract_characters(self, phase_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """キャラクター情報の抽出"""
        for result in phase_results:
            if result.get("phase_number") == 2:  # キャラクターフェーズ
                content = result.get("content", {})
                return content.get("characters", [])
        return []
    
    def _extract_story_structure(self, phase_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """ストーリー構造の抽出"""
        for result in phase_results:
            if result.get("phase_number") == 3:  # プロットフェーズ
                content = result.get("content", {})
                return content.get("story_structure", {})
        return {}
    
    def _calculate_total_time(self, phase_results: List[Dict[str, Any]]) -> float:
        """総生成時間の計算"""
        total_time = 0.0
        for result in phase_results:
            total_time += result.get("processing_time_seconds", 0.0)
        return total_time