"""Visual Generation Processor for Phase 2."""

import random
from typing import Dict, List, Any, Optional
from app.core.logging import LoggerMixin
from ..schemas import (
    CharacterAppearance,
    StyleGuide,
    VisualStyleType,
    HairColorType,
    EyeColorType,
    HeightType,
    BuildType,
    VISUAL_STYLES
)


class VisualGenerator(LoggerMixin):
    """Generates visual descriptions and style guides for characters."""

    def __init__(self):
        """Initialize visual generator."""
        super().__init__()

        # Color palettes by genre
        self.genre_palettes = {
            "fantasy": {
                "primary": ["#4A90E2", "#7B68EE", "#9370DB"],
                "secondary": ["#FFD700", "#FFA500", "#FF6347"],
                "accent": ["#32CD32", "#20B2AA", "#FF1493"]
            },
            "romance": {
                "primary": ["#FFB6C1", "#FFC0CB", "#FF69B4"],
                "secondary": ["#E6E6FA", "#DDA0DD", "#DA70D6"],
                "accent": ["#F0E68C", "#FFE4B5", "#FFDEAD"]
            },
            "action": {
                "primary": ["#DC143C", "#FF4500", "#FF6347"],
                "secondary": ["#4B0082", "#483D8B", "#6A5ACD"],
                "accent": ["#FFD700", "#FFA500", "#FF8C00"]
            },
            "mystery": {
                "primary": ["#2F4F4F", "#708090", "#778899"],
                "secondary": ["#4682B4", "#5F9EA0", "#6495ED"],
                "accent": ["#B22222", "#8B0000", "#A52A2A"]
            },
            "slice_of_life": {
                "primary": ["#98FB98", "#87CEEB", "#DDA0DD"],
                "secondary": ["#F0E68C", "#FFE4B5", "#FFDAB9"],
                "accent": ["#FF6347", "#4169E1", "#32CD32"]
            },
            "sci_fi": {
                "primary": ["#00CED1", "#4169E1", "#8A2BE2"],
                "secondary": ["#00FF7F", "#7FFF00", "#ADFF2F"],
                "accent": ["#FF1493", "#FF4500", "#FFD700"]
            },
            "horror": {
                "primary": ["#8B0000", "#4B0082", "#2F4F4F"],
                "secondary": ["#696969", "#808080", "#A9A9A9"],
                "accent": ["#DC143C", "#B22222", "#8B008B"]
            }
        }

        # Hair color mapping by role
        self.hair_color_map = {
            "protagonist": ["black", "brown", "blonde"],
            "sidekick": ["brown", "red", "blonde"],
            "antagonist": ["black", "white", "silver"],
            "mentor": ["white", "silver", "black"],
            "love_interest": ["brown", "blonde", "black"],
            "supporting": ["brown", "black"]
        }

        # Eye color mapping by role
        self.eye_color_map = {
            "protagonist": ["brown", "blue", "green"],
            "antagonist": ["red", "violet", "gold"],
            "sidekick": ["brown", "black", "blue"],
            "mentor": ["gray", "blue", "brown"],
            "love_interest": ["brown", "blue", "green"],
            "supporting": ["brown", "black"]
        }

        # Hair style templates
        self.hair_styles = {
            ("male", "protagonist"): "ショート・スパイキー",
            ("female", "protagonist"): "ミディアム・ストレート",
            ("male", "antagonist"): "ロング・ストレート",
            ("female", "antagonist"): "ロング・ウェーブ",
            ("male", "sidekick"): "ショート・カジュアル",
            ("female", "sidekick"): "ショート・ボブ",
            ("male", "mentor"): "ショート・整髪",
            ("female", "mentor"): "ミディアム・まとめ髪",
            ("male", "love_interest"): "ミディアム・ナチュラル",
            ("female", "love_interest"): "ロング・カール"
        }

        # Clothing styles by world setting and role
        self.clothing_styles = {
            "modern": {
                "protagonist": "カジュアル・学生服",
                "antagonist": "フォーマル・スーツ",
                "sidekick": "カジュアル・親しみやすい",
                "mentor": "フォーマル・落ち着いた",
                "love_interest": "おしゃれ・魅力的"
            },
            "fantasy": {
                "protagonist": "冒険者の装備",
                "antagonist": "ダークな魔法使いの衣装",
                "sidekick": "軽装の冒険装備",
                "mentor": "賢者のローブ",
                "love_interest": "エレガントなドレス"
            },
            "historical": {
                "protagonist": "時代に適した一般的な服装",
                "antagonist": "権力者の豪華な衣装",
                "sidekick": "庶民的な実用的な服装",
                "mentor": "知識人らしい装い",
                "love_interest": "美しい伝統的な装い"
            }
        }

        # Distinctive features by archetype
        self.distinctive_features = {
            "protagonist": ["意志の強い目", "真っ直ぐな姿勢", "親しみやすい笑顔"],
            "antagonist": ["鋭い眼光", "威圧的な雰囲気", "冷たい微笑"],
            "sidekick": ["表情豊か", "元気な雰囲気", "親しみやすい外見"],
            "mentor": ["落ち着いた表情", "知的な雰囲気", "品格のある立ち振る舞い"],
            "love_interest": ["美しい瞳", "優雅な仕草", "魅力的な笑顔"],
            "supporting": ["個性的な特徴", "記憶に残る外見", "役割に適した雰囲気"]
        }

    async def generate_character_appearances(
        self,
        characters: List[Dict[str, Any]],
        genre: str,
        world_setting: Dict[str, Any]
    ) -> List[CharacterAppearance]:
        """Generate visual appearances for all characters."""

        self.logger.info(f"Generating appearances for {len(characters)} characters")

        appearances = []
        for character in characters:
            appearance = await self._create_character_appearance(character, genre, world_setting)
            appearances.append(appearance)

        return appearances

    async def _create_character_appearance(
        self,
        character: Dict[str, Any],
        genre: str,
        world_setting: Dict[str, Any]
    ) -> CharacterAppearance:
        """Create appearance for a single character."""

        archetype = character.get("archetype", "supporting")
        gender = character.get("gender", "unknown")
        age = character.get("age_specific", 18)

        # Generate hair
        hair_color = self._generate_hair_color(archetype, genre)
        hair_style = self._generate_hair_style(archetype, gender)

        # Generate eyes
        eye_color = self._generate_eye_color(archetype)

        # Generate body characteristics
        height = self._determine_height(age, archetype)
        build = self._determine_build(archetype, genre)

        # Generate distinctive features
        distinctive_features = self._generate_distinctive_features(archetype)

        # Generate clothing
        clothing_style = self._generate_clothing_style(world_setting, archetype)

        # Generate expression
        default_expression = self._determine_default_expression(character.get("personality", {}))

        # Determine visual age
        age_appearance = self._determine_age_appearance(age)

        return CharacterAppearance(
            hair_color=hair_color,
            hair_style=hair_style,
            eye_color=eye_color,
            height=height,
            build=build,
            distinctive_features=distinctive_features,
            clothing_style=clothing_style,
            default_expression=default_expression,
            age_appearance=age_appearance
        )

    def create_style_guide(
        self,
        genre: str,
        target_audience: str,
        themes: List[str]
    ) -> StyleGuide:
        """Create comprehensive style guide for the manga."""

        self.logger.info(f"Creating style guide for {genre} genre, {target_audience} audience")

        # Determine overall visual style
        overall_style = self._determine_visual_style(genre, target_audience)

        # Generate color palette
        color_palette = self._generate_color_palette(genre, themes)

        # Create design principles
        design_principles = self._create_design_principles(genre, target_audience)

        # Generate consistency notes
        consistency_notes = self._create_consistency_notes(overall_style)

        # Add reference notes
        reference_notes = self._create_reference_notes(genre, overall_style)

        return StyleGuide(
            overall_style=overall_style,
            color_palette=color_palette,
            design_principles=design_principles,
            consistency_notes=consistency_notes,
            reference_notes=reference_notes
        )

    def _generate_hair_color(self, archetype: str, genre: str) -> HairColorType:
        """Generate appropriate hair color for character."""

        # Get base colors for archetype
        base_colors = self.hair_color_map.get(archetype, ["brown", "black"])

        # Fantasy allows more exotic colors
        if genre == "fantasy":
            exotic_colors = ["blue", "green", "purple", "pink"]
            if archetype in ["antagonist", "love_interest"]:
                base_colors.extend(exotic_colors)

        # Sci-fi allows unusual colors
        elif genre == "sci_fi":
            if archetype != "mentor":
                base_colors.extend(["silver", "blue", "green"])

        # Select random color from options
        selected_color = random.choice(base_colors)

        # Convert to enum
        try:
            return HairColorType(selected_color)
        except ValueError:
            return HairColorType.BROWN  # Fallback

    def _generate_eye_color(self, archetype: str) -> EyeColorType:
        """Generate eye color based on character archetype."""

        colors = self.eye_color_map.get(archetype, ["brown", "black"])
        selected_color = random.choice(colors)

        try:
            return EyeColorType(selected_color)
        except ValueError:
            return EyeColorType.BROWN  # Fallback

    def _generate_hair_style(self, archetype: str, gender: str) -> str:
        """Generate hair style based on archetype and gender."""

        # Clean archetype name (remove enum prefix if present)
        clean_archetype = archetype.replace("CharacterArchetypeType.", "").lower()

        key = (gender, clean_archetype)

        return self.hair_styles.get(key, self.hair_styles.get((gender, "protagonist"), "ミディアム"))

    def _determine_height(self, age: int, archetype: str) -> HeightType:
        """Determine character height based on age and role."""

        if age < 12:
            return HeightType.VERY_SHORT
        elif age < 16:
            return HeightType.SHORT if archetype == "sidekick" else HeightType.AVERAGE
        else:
            if archetype == "mentor":
                return HeightType.TALL
            elif archetype == "antagonist":
                return HeightType.TALL
            elif archetype == "protagonist":
                return HeightType.AVERAGE
            else:
                return HeightType.AVERAGE

    def _determine_build(self, archetype: str, genre: str) -> BuildType:
        """Determine character build based on archetype and genre."""

        build_map = {
            "protagonist": BuildType.ATHLETIC if genre in ["action", "fantasy"] else BuildType.AVERAGE,
            "antagonist": BuildType.MUSCULAR if genre == "action" else BuildType.AVERAGE,
            "sidekick": BuildType.SLIM,
            "mentor": BuildType.AVERAGE,
            "love_interest": BuildType.SLIM,
            "supporting": BuildType.AVERAGE
        }

        return build_map.get(archetype, BuildType.AVERAGE)

    def _generate_distinctive_features(self, archetype: str) -> List[str]:
        """Generate distinctive features for character."""

        features = self.distinctive_features.get(archetype, ["個性的な外見"])

        # Select 1-3 features
        num_features = min(3, max(1, len(features)))
        return random.sample(features, num_features)

    def _generate_clothing_style(self, world_setting: Dict[str, Any], archetype: str) -> str:
        """Generate clothing style based on world setting and archetype."""

        # Determine world type
        time_period = world_setting.get("time_period", "modern")
        if time_period == "fantasy":
            world_type = "fantasy"
        elif time_period in ["past", "historical"]:
            world_type = "historical"
        else:
            world_type = "modern"

        clothing_map = self.clothing_styles.get(world_type, self.clothing_styles["modern"])
        return clothing_map.get(archetype, "一般的な服装")

    def _determine_default_expression(self, personality: Dict[str, Any]) -> str:
        """Determine character's default facial expression."""

        main_traits = personality.get("main_traits", [])
        if not main_traits:
            return "中性的な表情"

        # Extract trait names
        trait_names = []
        for trait in main_traits:
            if isinstance(trait, dict):
                trait_names.append(trait.get("trait", ""))
            else:
                trait_names.append(str(trait))

        # Map traits to expressions
        if any("明るい" in trait or "元気" in trait for trait in trait_names):
            return "笑顔"
        elif any("冷静" in trait or "クール" in trait for trait in trait_names):
            return "冷静な表情"
        elif any("優しい" in trait or "思いやり" in trait for trait in trait_names):
            return "優しい表情"
        elif any("真剣" in trait or "決意" in trait for trait in trait_names):
            return "真剣な表情"
        else:
            return "自然な表情"

    def _determine_age_appearance(self, age: int) -> str:
        """Determine how old the character appears."""

        if age < 10:
            return "幼児"
        elif age < 13:
            return "子供"
        elif age < 18:
            return "少年・少女"
        elif age < 25:
            return "青年"
        elif age < 40:
            return "大人"
        elif age < 60:
            return "中年"
        else:
            return "高齢者"

    def _determine_visual_style(self, genre: str, target_audience: str) -> VisualStyleType:
        """Determine overall visual art style."""

        if target_audience == "children":
            return VisualStyleType.KODOMO
        elif target_audience == "teens":
            if genre in ["action", "fantasy", "sci_fi"]:
                return VisualStyleType.SHOUNEN
            elif genre in ["romance", "slice_of_life"]:
                return VisualStyleType.SHOUJO
            else:
                return VisualStyleType.SHOUNEN
        elif target_audience in ["young_adults", "adults"]:
            if genre in ["romance", "slice_of_life"] and target_audience == "young_adults":
                return VisualStyleType.JOSEI
            else:
                return VisualStyleType.SEINEN
        else:
            return VisualStyleType.SHOUNEN  # Default

    def _generate_color_palette(self, genre: str, themes: List[str]) -> Dict[str, str]:
        """Generate color palette for the manga."""

        # Get base palette for genre
        palette_data = self.genre_palettes.get(genre, self.genre_palettes["slice_of_life"])

        # Convert to flat dictionary with string keys
        color_palette = {}

        # Add primary colors
        for i, color in enumerate(palette_data["primary"]):
            color_palette[f"primary_{i+1}"] = color

        # Add secondary colors
        for i, color in enumerate(palette_data["secondary"]):
            color_palette[f"secondary_{i+1}"] = color

        # Add accent colors
        for i, color in enumerate(palette_data["accent"]):
            color_palette[f"accent_{i+1}"] = color

        # Add theme-based adjustments
        if "暗い" in themes or "シリアス" in themes:
            color_palette["mood_primary"] = "#2F4F4F"
            color_palette["mood_secondary"] = "#696969"
        elif "明るい" in themes or "楽しい" in themes:
            color_palette["mood_primary"] = "#FFD700"
            color_palette["mood_secondary"] = "#87CEEB"

        return color_palette

    def _create_design_principles(self, genre: str, target_audience: str) -> List[str]:
        """Create design principles for consistency."""

        base_principles = [
            "キャラクターの個性を視覚的に表現",
            "ジャンルに適した表現スタイル",
            "読みやすさを最優先",
            "感情表現の豊かさ"
        ]

        # Add genre-specific principles
        if genre == "action":
            base_principles.extend([
                "動的なポーズと表現",
                "エネルギッシュなライン",
                "迫力のある構図"
            ])
        elif genre == "romance":
            base_principles.extend([
                "美しく魅力的なキャラクター",
                "感情的な表現の繊細さ",
                "ロマンチックな雰囲気"
            ])
        elif genre == "fantasy":
            base_principles.extend([
                "幻想的で創造的なデザイン",
                "魔法的要素の表現",
                "異世界感の演出"
            ])

        # Add audience-specific principles
        if target_audience == "children":
            base_principles.extend([
                "シンプルで分かりやすいデザイン",
                "明るく親しみやすい表現"
            ])
        elif target_audience in ["young_adults", "adults"]:
            base_principles.extend([
                "洗練された表現",
                "細部への注意",
                "大人の魅力の表現"
            ])

        return base_principles

    def _create_consistency_notes(self, visual_style: VisualStyleType) -> List[str]:
        """Create consistency notes based on visual style."""

        style_notes = {
            VisualStyleType.SHOUNEN: [
                "目は大きく表現力豊かに",
                "アクションシーンでは動的なライン",
                "表情は分かりやすく明確に"
            ],
            VisualStyleType.SHOUJO: [
                "目は大きく、まつげを強調",
                "花や装飾要素を効果的に使用",
                "感情表現は繊細に"
            ],
            VisualStyleType.SEINEN: [
                "リアルな体のプロポーション",
                "詳細な背景と陰影",
                "成熟した表現"
            ],
            VisualStyleType.KODOMO: [
                "シンプルで丸みのあるデザイン",
                "明るい色使い",
                "親しみやすいキャラクター"
            ],
            VisualStyleType.JOSEI: [
                "洗練された大人の魅力",
                "繊細な線と表現",
                "情緒的な深み"
            ]
        }

        return style_notes.get(visual_style, [
            "ジャンルに適した表現を維持",
            "キャラクターの個性を保持",
            "読みやすさを重視"
        ])

    def _create_reference_notes(self, genre: str, visual_style: VisualStyleType) -> List[str]:
        """Create reference notes for artists."""

        return [
            f"{genre}ジャンルの代表的な作品を参考に",
            f"{visual_style.value}スタイルの特徴を活用",
            "キャラクターデザインの一貫性を保持",
            "表現の幅を広げつつ統一感を維持",
            "読者の年齢層に適した表現レベル"
        ]