"""Add HITL (Human-in-the-loop) support tables

Revision ID: 0007_add_hitl_tables
Revises: 0006_add_user_tables
Create Date: 2025-09-20 10:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0007_add_hitl_tables"
down_revision = "0006_add_user_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_feedback_history table for detailed feedback tracking
    op.create_table(
        "user_feedback_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True),
                 sa.ForeignKey("manga_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("phase", sa.Integer(), nullable=False),
        sa.Column("feedback_type", sa.String(length=50), nullable=False),  # approval, modification, skip
        sa.Column("feedback_data", sa.JSON(), nullable=True),  # structured feedback data
        sa.Column("user_satisfaction_score", sa.Float(), nullable=True),  # 1-5 rating
        sa.Column("natural_language_input", sa.Text(), nullable=True),  # free text feedback
        sa.Column("selected_options", postgresql.ARRAY(sa.String()), nullable=True),  # selected feedback options
        sa.Column("processing_time_ms", sa.Integer(), nullable=True),  # time to provide feedback
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("processing_completed_at", sa.DateTime(), nullable=True),  # when feedback was processed
    )

    # Create phase_feedback_states table for tracking waiting states
    op.create_table(
        "phase_feedback_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True),
                 sa.ForeignKey("manga_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("phase", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(length=50), nullable=False),  # waiting, received, processing, completed, timeout
        sa.Column("preview_data", sa.JSON(), nullable=True),  # preview data for user
        sa.Column("feedback_started_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("feedback_timeout_at", sa.DateTime(), nullable=True),  # 30 minutes after start
        sa.Column("feedback_received_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("session_id", "phase", name="uq_phase_feedback_states_session_phase"),
    )

    # Create feedback_option_templates table for phase-specific feedback options
    op.create_table(
        "feedback_option_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("phase", sa.Integer(), nullable=False),
        sa.Column("option_key", sa.String(length=100), nullable=False),  # theme_modify, genre_change, etc.
        sa.Column("option_label", sa.Text(), nullable=False),  # "テーマ修正", "ジャンル変更", etc.
        sa.Column("option_description", sa.Text(), nullable=True),
        sa.Column("option_category", sa.String(length=50), nullable=True),  # content, style, structure
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("phase", "option_key", name="uq_feedback_option_templates_phase_key"),
    )

    # Extend manga_sessions table with HITL fields
    op.add_column("manga_sessions", sa.Column("waiting_for_feedback", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("manga_sessions", sa.Column("feedback_timeout_at", sa.DateTime(), nullable=True))
    op.add_column("manga_sessions", sa.Column("total_feedback_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("manga_sessions", sa.Column("hitl_enabled", sa.Boolean(), nullable=False, server_default="false"))

    # Extend phase_results table with feedback integration fields
    op.add_column("phase_results", sa.Column("feedback_integrated", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("phase_results", sa.Column("user_satisfaction_score", sa.Float(), nullable=True))
    op.add_column("phase_results", sa.Column("combined_quality_score", sa.Float(), nullable=True))  # AI + User score
    op.add_column("phase_results", sa.Column("feedback_summary", sa.Text(), nullable=True))

    # Create indexes for performance
    op.create_index("ix_user_feedback_history_session_id", "user_feedback_history", ["session_id"])
    op.create_index("ix_user_feedback_history_phase", "user_feedback_history", ["phase"])
    op.create_index("ix_user_feedback_history_created_at", "user_feedback_history", ["created_at"])

    op.create_index("ix_phase_feedback_states_session_id", "phase_feedback_states", ["session_id"])
    op.create_index("ix_phase_feedback_states_state", "phase_feedback_states", ["state"])
    op.create_index("ix_phase_feedback_states_timeout", "phase_feedback_states", ["feedback_timeout_at"])

    op.create_index("ix_feedback_option_templates_phase", "feedback_option_templates", ["phase"])
    op.create_index("ix_feedback_option_templates_active", "feedback_option_templates", ["is_active"])

    # Insert default feedback options for each phase
    _insert_default_feedback_options()


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_feedback_option_templates_active", table_name="feedback_option_templates")
    op.drop_index("ix_feedback_option_templates_phase", table_name="feedback_option_templates")
    op.drop_index("ix_phase_feedback_states_timeout", table_name="phase_feedback_states")
    op.drop_index("ix_phase_feedback_states_state", table_name="phase_feedback_states")
    op.drop_index("ix_phase_feedback_states_session_id", table_name="phase_feedback_states")
    op.drop_index("ix_user_feedback_history_created_at", table_name="user_feedback_history")
    op.drop_index("ix_user_feedback_history_phase", table_name="user_feedback_history")
    op.drop_index("ix_user_feedback_history_session_id", table_name="user_feedback_history")

    # Drop added columns
    op.drop_column("phase_results", "feedback_summary")
    op.drop_column("phase_results", "combined_quality_score")
    op.drop_column("phase_results", "user_satisfaction_score")
    op.drop_column("phase_results", "feedback_integrated")

    op.drop_column("manga_sessions", "hitl_enabled")
    op.drop_column("manga_sessions", "total_feedback_count")
    op.drop_column("manga_sessions", "feedback_timeout_at")
    op.drop_column("manga_sessions", "waiting_for_feedback")

    # Drop tables
    op.drop_table("feedback_option_templates")
    op.drop_table("phase_feedback_states")
    op.drop_table("user_feedback_history")


def _insert_default_feedback_options() -> None:
    """Insert default feedback options for each phase"""

    # Phase 1: Concept Analysis feedback options
    phase1_options = [
        (1, "theme_modify", "テーマ修正", "物語のテーマを調整したい", "content", 1),
        (1, "genre_change", "ジャンル変更", "ジャンルを変更したい", "content", 2),
        (1, "world_setting_adjust", "世界観調整", "世界設定を修正したい", "content", 3),
        (1, "tone_change", "雰囲気変更", "作品の雰囲気を変えたい", "style", 4),
        (1, "target_audience_adjust", "対象読者層調整", "想定読者を変更したい", "content", 5),
    ]

    # Phase 2: Character Design feedback options
    phase2_options = [
        (2, "character_add", "キャラクター追加", "新しいキャラクターを追加したい", "content", 1),
        (2, "character_remove", "キャラクター削除", "キャラクターを削除したい", "content", 2),
        (2, "personality_change", "性格変更", "キャラクターの性格を変更したい", "content", 3),
        (2, "visual_adjust", "ビジュアル調整", "キャラクターの見た目を調整したい", "style", 4),
        (2, "relationship_modify", "関係性修正", "キャラクター同士の関係を修正したい", "content", 5),
    ]

    # Phase 3: Story Structure feedback options
    phase3_options = [
        (3, "plot_change", "プロット変更", "物語の展開を変更したい", "structure", 1),
        (3, "pacing_adjust", "ペーシング調整", "物語のテンポを調整したい", "structure", 2),
        (3, "climax_modify", "クライマックス修正", "物語の盛り上がりを修正したい", "structure", 3),
        (3, "scene_add", "シーン追加", "新しいシーンを追加したい", "content", 4),
        (3, "scene_remove", "シーン削除", "不要なシーンを削除したい", "content", 5),
    ]

    # Phase 4: Panel Layout feedback options
    phase4_options = [
        (4, "layout_change", "レイアウト変更", "コマ割りを変更したい", "structure", 1),
        (4, "panel_size_adjust", "コマサイズ調整", "コマの大きさを調整したい", "structure", 2),
        (4, "camera_angle_change", "カメラアングル変更", "視点を変更したい", "style", 3),
        (4, "composition_modify", "構図修正", "画面構成を修正したい", "style", 4),
        (4, "page_count_adjust", "ページ数調整", "ページ数を調整したい", "structure", 5),
    ]

    # Phase 5: Scene Imagery feedback options
    phase5_options = [
        (5, "image_regenerate", "画像再生成", "画像を作り直したい", "content", 1),
        (5, "style_adjust", "スタイル調整", "画像のスタイルを調整したい", "style", 2),
        (5, "detail_add", "詳細追加", "画像に詳細を追加したい", "content", 3),
        (5, "background_change", "背景変更", "背景を変更したい", "content", 4),
        (5, "character_pose_adjust", "キャラポーズ調整", "キャラクターのポーズを調整したい", "style", 5),
    ]

    # Phase 6: Dialogue Layout feedback options
    phase6_options = [
        (6, "dialogue_modify", "セリフ修正", "セリフを修正したい", "content", 1),
        (6, "dialogue_add", "セリフ追加", "セリフを追加したい", "content", 2),
        (6, "dialogue_remove", "セリフ削除", "セリフを削除したい", "content", 3),
        (6, "bubble_style_change", "吹き出しスタイル変更", "吹き出しのスタイルを変更したい", "style", 4),
        (6, "text_position_adjust", "テキスト位置調整", "文字の位置を調整したい", "style", 5),
        (6, "sound_effect_modify", "効果音修正", "効果音を修正したい", "content", 6),
    ]

    # Phase 7: Final Composition feedback options
    phase7_options = [
        (7, "overall_quality_improve", "全体品質向上", "全体的な品質を向上させたい", "quality", 1),
        (7, "consistency_check", "一貫性チェック", "作品の一貫性を確認したい", "quality", 2),
        (7, "final_polish", "最終仕上げ", "最終的な仕上げを行いたい", "quality", 3),
        (7, "page_order_adjust", "ページ順序調整", "ページの順序を調整したい", "structure", 4),
        (7, "readability_improve", "可読性向上", "読みやすさを向上させたい", "quality", 5),
    ]

    # Combine all options
    all_options = (phase1_options + phase2_options + phase3_options +
                  phase4_options + phase5_options + phase6_options + phase7_options)

    # Insert options
    feedback_options_table = sa.table(
        "feedback_option_templates",
        sa.column("phase", sa.Integer),
        sa.column("option_key", sa.String),
        sa.column("option_label", sa.Text),
        sa.column("option_description", sa.Text),
        sa.column("option_category", sa.String),
        sa.column("display_order", sa.Integer),
    )

    for phase, key, label, desc, category, order in all_options:
        op.execute(
            feedback_options_table.insert().values(
                phase=phase,
                option_key=key,
                option_label=label,
                option_description=desc,
                option_category=category,
                display_order=order,
            )
        )