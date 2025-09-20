from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class FeedbackOptionTemplate(Base):
    """Feedback option templates for HITL system"""

    __tablename__ = "feedback_option_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phase = Column(Integer, nullable=False)
    option_key = Column(String(100), nullable=False)  # theme_modify, genre_change, etc.
    option_label = Column(Text, nullable=False)  # "テーマ修正", "ジャンル変更", etc.
    option_description = Column(Text, nullable=True)
    option_category = Column(String(50), nullable=True)  # content, style, structure, quality
    is_active = Column(Boolean, nullable=False, default=True)
    display_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Constraints
    __table_args__ = (
        UniqueConstraint("phase", "option_key", name="uq_feedback_option_templates_phase_key"),
    )

    def __repr__(self) -> str:
        return f"<FeedbackOptionTemplate(phase={self.phase}, key={self.option_key}, label={self.option_label})>"

    @classmethod
    def get_phase_options(cls, phase: int, session, only_active: bool = True) -> List[FeedbackOptionTemplate]:
        """Get all feedback options for a specific phase"""
        query = session.query(cls).filter(cls.phase == phase)
        if only_active:
            query = query.filter(cls.is_active == True)
        return query.order_by(cls.display_order, cls.option_label).all()

    @classmethod
    def get_option_by_key(cls, phase: int, option_key: str, session) -> Optional[FeedbackOptionTemplate]:
        """Get feedback option by phase and key"""
        return session.query(cls).filter(
            cls.phase == phase,
            cls.option_key == option_key,
            cls.is_active == True
        ).first()

    @classmethod
    def get_options_by_category(
        cls,
        phase: int,
        category: str,
        session,
        only_active: bool = True
    ) -> List[FeedbackOptionTemplate]:
        """Get feedback options by phase and category"""
        query = session.query(cls).filter(
            cls.phase == phase,
            cls.option_category == category
        )
        if only_active:
            query = query.filter(cls.is_active == True)
        return query.order_by(cls.display_order, cls.option_label).all()

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "phase": self.phase,
            "option_key": self.option_key,
            "option_label": self.option_label,
            "option_description": self.option_description,
            "option_category": self.option_category,
            "display_order": self.display_order,
            "is_active": self.is_active
        }

    @classmethod
    def create_default_options_for_phase(cls, phase: int) -> List[FeedbackOptionTemplate]:
        """Create default feedback options for a specific phase"""

        # Phase-specific default options
        phase_options = {
            1: [  # Concept Analysis
                ("theme_modify", "テーマ修正", "物語のテーマを調整したい", "content", 1),
                ("genre_change", "ジャンル変更", "ジャンルを変更したい", "content", 2),
                ("world_setting_adjust", "世界観調整", "世界設定を修正したい", "content", 3),
                ("tone_change", "雰囲気変更", "作品の雰囲気を変えたい", "style", 4),
            ],
            2: [  # Character Design
                ("character_add", "キャラクター追加", "新しいキャラクターを追加したい", "content", 1),
                ("character_remove", "キャラクター削除", "キャラクターを削除したい", "content", 2),
                ("personality_change", "性格変更", "キャラクターの性格を変更したい", "content", 3),
                ("visual_adjust", "ビジュアル調整", "キャラクターの見た目を調整したい", "style", 4),
            ],
            3: [  # Story Structure
                ("plot_change", "プロット変更", "物語の展開を変更したい", "structure", 1),
                ("pacing_adjust", "ペーシング調整", "物語のテンポを調整したい", "structure", 2),
                ("climax_modify", "クライマックス修正", "物語の盛り上がりを修正したい", "structure", 3),
            ],
            4: [  # Panel Layout
                ("layout_change", "レイアウト変更", "コマ割りを変更したい", "structure", 1),
                ("panel_size_adjust", "コマサイズ調整", "コマの大きさを調整したい", "structure", 2),
                ("camera_angle_change", "カメラアングル変更", "視点を変更したい", "style", 3),
            ],
            5: [  # Scene Imagery
                ("image_regenerate", "画像再生成", "画像を作り直したい", "content", 1),
                ("style_adjust", "スタイル調整", "画像のスタイルを調整したい", "style", 2),
                ("detail_add", "詳細追加", "画像に詳細を追加したい", "content", 3),
            ],
            6: [  # Dialogue Layout
                ("dialogue_modify", "セリフ修正", "セリフを修正したい", "content", 1),
                ("dialogue_add", "セリフ追加", "セリフを追加したい", "content", 2),
                ("bubble_style_change", "吹き出しスタイル変更", "吹き出しのスタイルを変更したい", "style", 3),
            ],
            7: [  # Final Composition
                ("overall_quality_improve", "全体品質向上", "全体的な品質を向上させたい", "quality", 1),
                ("consistency_check", "一貫性チェック", "作品の一貫性を確認したい", "quality", 2),
                ("final_polish", "最終仕上げ", "最終的な仕上げを行いたい", "quality", 3),
            ]
        }

        options = []
        for key, label, desc, category, order in phase_options.get(phase, []):
            option = cls(
                phase=phase,
                option_key=key,
                option_label=label,
                option_description=desc,
                option_category=category,
                display_order=order
            )
            options.append(option)

        return options