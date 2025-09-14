"""Phase 6: Dialogue Generator.

This module handles the core dialogue generation logic for manga panels,
including character-specific dialogue creation and narrative text generation.
"""

from typing import Dict, Any, List, Optional, Tuple
import asyncio
import logging

from ..schemas import (
    DialogueElement, NarrationElement, PanelDialogue,
    DialogueType, SpeechPattern, ImportanceLevel, NarrationStyle,
    DialogueCharacteristics, DialogueGenerationTask,
    PlacementPosition
)


logger = logging.getLogger(__name__)


class DialogueGenerator:
    """Core dialogue generation processor for Phase 6."""

    def __init__(self):
        """Initialize dialogue generator with patterns and templates."""

        # Dialogue type characteristics mapping
        self.dialogue_types = {
            "speech": DialogueCharacteristics(
                bubble_style="standard_speech",
                tail_style="pointed",
                text_size="normal",
                font_weight="normal"
            ),
            "thought": DialogueCharacteristics(
                bubble_style="cloud_thought",
                tail_style="bubbles",
                text_size="italic",
                font_weight="normal"
            ),
            "shout": DialogueCharacteristics(
                bubble_style="jagged_excitement",
                tail_style="lightning",
                text_size="large",
                font_weight="bold"
            ),
            "whisper": DialogueCharacteristics(
                bubble_style="dotted_soft",
                tail_style="small_curved",
                text_size="small",
                font_weight="light"
            ),
            "narration": DialogueCharacteristics(
                bubble_style="rectangular_box",
                tail_style="none",
                text_size="normal",
                font_weight="normal"
            )
        }

        # Dialogue templates by context
        self.introduction_templates = {
            "friendly": [
                "よろしくお願いします！",
                "初めまして、{}です。",
                "こんにちは！"
            ],
            "serious": [
                "私は{}です。",
                "{}と申します。",
                "お初にお目にかかります。"
            ],
            "casual": [
                "{}だよ！",
                "よろしく〜",
                "はじめまして！"
            ]
        }

        self.response_templates = {
            "curiosity": ["そうなんですね", "興味深いです", "へえ〜"],
            "engagement": ["なるほど", "そうですね", "分かります"],
            "concern": ["大丈夫ですか？", "心配です", "どうしたんですか？"],
            "tension": ["え？", "まさか...", "そんな..."],
            "relief": ["良かった", "安心しました", "ほっとしました"]
        }

        self.general_templates = {
            "curious": "それは...",
            "neutral": "そうですね。",
            "positive": "いいですね！",
            "negative": "うーん..."
        }

        # Default reading speed (syllables per second)
        self.reading_speed = 3.5

    async def generate_panel_dialogue(
        self,
        task: DialogueGenerationTask
    ) -> PanelDialogue:
        """Generate complete dialogue for a single panel.

        Args:
            task: Dialogue generation task specification

        Returns:
            Complete panel dialogue with elements and timing
        """

        try:
            # Generate dialogue elements for characters
            dialogue_elements = await self._generate_panel_dialogue_elements(
                task.characters,
                task.scene_context,
                task.emotional_tone,
                task.panel_specs.get("genre", "general"),
                task.panel_id
            )

            # Generate narration if needed
            narration = await self._generate_panel_narration(
                task.scene_context,
                task.panel_specs,
                dialogue_elements
            )

            # Calculate reading time
            estimated_reading_time = self._estimate_panel_reading_time(
                dialogue_elements, narration
            )

            # Count total elements
            total_elements = len(dialogue_elements) + (1 if narration else 0)

            return PanelDialogue(
                panel_id=task.panel_id,
                scene_number=task.scene_number,
                dialogue_elements=dialogue_elements,
                narration=narration,
                total_text_elements=total_elements,
                estimated_reading_time=estimated_reading_time
            )

        except Exception as e:
            logger.error(f"Error generating dialogue for panel {task.panel_id}: {e}")
            # Return minimal dialogue in case of error
            return PanelDialogue(
                panel_id=task.panel_id,
                scene_number=task.scene_number,
                dialogue_elements=[],
                narration=None,
                total_text_elements=0,
                estimated_reading_time=0.0
            )

    async def generate_batch_dialogues(
        self,
        tasks: List[DialogueGenerationTask]
    ) -> List[PanelDialogue]:
        """Generate dialogues for multiple panels in batch.

        Args:
            tasks: List of dialogue generation tasks

        Returns:
            List of completed panel dialogues
        """

        # Process panels concurrently for better performance
        dialogue_futures = [
            self.generate_panel_dialogue(task) for task in tasks
        ]

        dialogues = await asyncio.gather(*dialogue_futures, return_exceptions=True)

        # Handle any exceptions and ensure we return valid dialogues
        valid_dialogues = []
        for i, dialogue in enumerate(dialogues):
            if isinstance(dialogue, Exception):
                logger.error(f"Error processing panel {tasks[i].panel_id}: {dialogue}")
                # Create empty dialogue for failed panel
                dialogue = PanelDialogue(
                    panel_id=tasks[i].panel_id,
                    scene_number=tasks[i].scene_number,
                    dialogue_elements=[],
                    narration=None,
                    total_text_elements=0,
                    estimated_reading_time=0.0
                )
            valid_dialogues.append(dialogue)

        return valid_dialogues

    async def _generate_panel_dialogue_elements(
        self,
        characters: List[Dict[str, Any]],
        scene_context: Dict[str, Any],
        emotional_tone: str,
        genre: str,
        panel_id: str
    ) -> List[DialogueElement]:
        """Generate dialogue elements for characters in a panel."""

        dialogue_elements = []

        if not characters:
            return dialogue_elements

        # Determine scene purpose and pacing
        scene_purpose = scene_context.get("purpose", "")
        scene_pacing = scene_context.get("pacing", "medium")

        # Generate dialogue for each character
        for i, character in enumerate(characters):
            char_name = character.get("name", f"Character{i+1}")

            # Generate appropriate dialogue
            dialogue_text = await self._generate_character_dialogue(
                character, scene_context, emotional_tone, genre, i == 0
            )

            if dialogue_text:
                # Determine dialogue type based on context
                dialogue_type = self._determine_dialogue_type(
                    dialogue_text, emotional_tone, scene_pacing
                )

                # Determine importance
                importance = self._determine_dialogue_importance(
                    dialogue_text, scene_purpose, i == 0
                )

                # Get speech pattern
                speech_pattern = self._get_character_speech_pattern(character)

                dialogue_element = DialogueElement(
                    speaker=char_name,
                    text=dialogue_text,
                    dialogue_type=DialogueType(dialogue_type),
                    emotion=emotional_tone,
                    importance=ImportanceLevel(importance),
                    text_length=len(dialogue_text),
                    estimated_syllables=self._estimate_syllables(dialogue_text),
                    speech_pattern=SpeechPattern(speech_pattern)
                )

                dialogue_elements.append(dialogue_element)

        return dialogue_elements

    async def _generate_character_dialogue(
        self,
        character: Dict[str, Any],
        scene_context: Dict[str, Any],
        emotional_tone: str,
        genre: str,
        is_primary_speaker: bool
    ) -> str:
        """Generate dialogue for a specific character."""

        character_name = character.get("name", "キャラクター")
        personality = character.get("personality", [])
        scene_purpose = scene_context.get("purpose", "")

        # Generate dialogue based on scene purpose
        if "introduction" in scene_purpose:
            if is_primary_speaker:
                dialogue = self._generate_introduction_dialogue(character_name, personality)
            else:
                dialogue = self._generate_response_dialogue(emotional_tone)
        elif "conflict" in scene_purpose:
            dialogue = self._generate_conflict_dialogue(character_name, personality, emotional_tone)
        elif "resolution" in scene_purpose:
            dialogue = self._generate_resolution_dialogue(emotional_tone, personality)
        else:
            dialogue = self._generate_general_dialogue(character_name, personality, emotional_tone)

        # Apply genre-specific modifications
        dialogue = self._apply_genre_dialogue_style(dialogue, genre, personality)

        # Ensure appropriate length
        dialogue = self._adjust_dialogue_length(dialogue, emotional_tone)

        return dialogue

    def _generate_introduction_dialogue(self, char_name: str, personality: List[str]) -> str:
        """Generate introduction dialogue."""

        # Determine style based on personality
        if any(trait in ["明るい", "友達想い", "元気"] for trait in personality):
            style = "friendly"
        elif any(trait in ["真剣", "冷静", "完璧主義"] for trait in personality):
            style = "serious"
        else:
            style = "casual"

        templates = self.introduction_templates.get(style, self.introduction_templates["casual"])
        template = templates[0]  # Use first template for simplicity

        if "{}" in template:
            return template.format(char_name)
        else:
            return template

    def _generate_response_dialogue(self, emotional_tone: str) -> str:
        """Generate response dialogue."""

        templates = self.response_templates.get(emotional_tone, ["そうですね"])
        return templates[0]

    def _generate_conflict_dialogue(
        self, char_name: str, personality: List[str], emotional_tone: str
    ) -> str:
        """Generate conflict dialogue."""

        if emotional_tone in ["tension", "anxiety"]:
            if "勇敢" in personality:
                return "負けるわけにはいかない！"
            elif "冷静" in personality:
                return "落ち着いて考えましょう。"
            else:
                return "どうしよう..."
        else:
            if "正義感が強い" in personality:
                return "これは間違っています！"
            else:
                return "困りましたね..."

    def _generate_resolution_dialogue(self, emotional_tone: str, personality: List[str]) -> str:
        """Generate resolution dialogue."""

        if emotional_tone in ["relief", "satisfaction"]:
            if "明るい" in personality:
                return "やったね！"
            else:
                return "良かった..."
        else:
            return "終わりましたね。"

    def _generate_general_dialogue(
        self, char_name: str, personality: List[str], emotional_tone: str
    ) -> str:
        """Generate general dialogue."""

        # Map emotional tone to general category
        if emotional_tone in ["curiosity", "engagement"]:
            return self.general_templates["curious"]
        elif emotional_tone in ["satisfaction", "relief"]:
            return self.general_templates["positive"]
        elif emotional_tone in ["tension", "anxiety"]:
            return self.general_templates["negative"]
        else:
            return self.general_templates["neutral"]

    def _apply_genre_dialogue_style(
        self, dialogue: str, genre: str, personality: List[str]
    ) -> str:
        """Apply genre-specific dialogue styling."""

        if genre == "action":
            # Make action dialogue more dynamic
            if "！" not in dialogue and len(dialogue) < 10:
                dialogue = dialogue.rstrip("。") + "！"
        elif genre == "romance":
            # Make romance dialogue softer
            if dialogue.endswith("！"):
                dialogue = dialogue.rstrip("！") + "..."
        elif genre == "mystery":
            # Add mystery atmosphere
            if len(dialogue) < 5:
                dialogue += "..."

        return dialogue

    def _adjust_dialogue_length(self, dialogue: str, emotional_tone: str) -> str:
        """Adjust dialogue length for readability."""

        # Maximum comfortable length for manga dialogue
        max_length = 25

        if len(dialogue) > max_length:
            # Truncate and add ellipsis
            dialogue = dialogue[:max_length-3] + "..."

        # Minimum length for some emotional tones
        if emotional_tone in ["tension", "climax"] and len(dialogue) < 5:
            dialogue += "！"

        return dialogue

    def _determine_dialogue_type(
        self, dialogue_text: str, emotional_tone: str, scene_pacing: str
    ) -> str:
        """Determine the type of dialogue bubble needed."""

        # Check for obvious indicators
        if dialogue_text.endswith("！") or dialogue_text.endswith("!"):
            if emotional_tone in ["tension", "climax"]:
                return "shout"
            else:
                return "speech"
        elif dialogue_text.endswith("..."):
            if "思" in dialogue_text or "考え" in dialogue_text:
                return "thought"
            else:
                return "whisper"
        elif "（" in dialogue_text or "）" in dialogue_text:
            return "thought"
        else:
            return "speech"

    def _determine_dialogue_importance(
        self, dialogue_text: str, scene_purpose: str, is_primary: bool
    ) -> str:
        """Determine the importance level of dialogue."""

        # Primary speakers in key scenes are high importance
        if is_primary and any(keyword in scene_purpose
                              for keyword in ["climax", "resolution", "conflict"]):
            return "high"

        # Long or emotional dialogue is medium importance
        if len(dialogue_text) > 15 or dialogue_text.endswith("！"):
            return "medium"

        return "low"

    def _get_character_speech_pattern(self, character: Dict[str, Any]) -> str:
        """Get character-specific speech pattern."""

        personality = character.get("personality", [])
        age = character.get("age", 18)

        if age < 16:
            return "youthful"
        elif any(trait in ["冷静", "知的", "完璧主義"] for trait in personality):
            return "formal"
        elif any(trait in ["明るい", "元気", "カジュアル"] for trait in personality):
            return "casual"
        else:
            return "standard"

    async def _generate_panel_narration(
        self,
        scene_context: Dict[str, Any],
        panel_specs: Dict[str, Any],
        dialogue_elements: List[DialogueElement]
    ) -> Optional[NarrationElement]:
        """Generate narration for panel if needed."""

        # Check if narration is needed
        scene_purpose = scene_context.get("purpose", "")
        camera_angle = panel_specs.get("camera_angle", "medium_shot")

        # Narration is useful for:
        # 1. Scene establishment (wide shots)
        # 2. Time/location changes
        # 3. Internal thoughts/feelings
        # 4. Action description

        needs_narration = (
            camera_angle in ["wide_shot", "bird_eye"] or
            "introduction" in scene_purpose or
            len(dialogue_elements) == 0
        )

        if not needs_narration:
            return None

        # Generate appropriate narration
        if "introduction" in scene_purpose:
            narration_text = self._generate_setting_narration(scene_context)
            style = NarrationStyle.DESCRIPTIVE
        elif camera_angle in ["wide_shot", "bird_eye"]:
            narration_text = self._generate_scene_description_narration(scene_context)
            style = NarrationStyle.ATMOSPHERIC
        elif len(dialogue_elements) == 0:
            narration_text = self._generate_action_narration(scene_context)
            style = NarrationStyle.ACTION
        else:
            return None

        if narration_text:
            return NarrationElement(
                text=narration_text,
                position=PlacementPosition.TOP,
                style=style,
                importance=ImportanceLevel.MEDIUM,
                text_length=len(narration_text)
            )

        return None

    def _generate_setting_narration(self, scene_context: Dict[str, Any]) -> str:
        """Generate setting/location narration."""
        location = scene_context.get("location", "")
        if location:
            return f"{location}にて..."
        return "物語の舞台..."

    def _generate_scene_description_narration(self, scene_context: Dict[str, Any]) -> str:
        """Generate scene description narration."""
        scene_purpose = scene_context.get("purpose", "")
        if "conflict" in scene_purpose:
            return "緊迫した状況が続く..."
        elif "peaceful" in scene_purpose:
            return "静かな時が流れる..."
        else:
            return "時は流れ..."

    def _generate_action_narration(self, scene_context: Dict[str, Any]) -> str:
        """Generate action description narration."""
        pacing = scene_context.get("pacing", "medium")
        if pacing == "fast":
            return "その時！"
        elif pacing == "slow":
            return "ゆっくりと..."
        else:
            return "そして..."

    def _estimate_syllables(self, text: str) -> int:
        """Estimate syllable count for Japanese text."""

        # Simple approximation: most Japanese characters are one syllable
        # Remove punctuation and spaces
        clean_text = ''.join(c for c in text if c.isalnum())
        return len(clean_text)

    def _estimate_panel_reading_time(
        self,
        dialogue_elements: List[DialogueElement],
        narration: Optional[NarrationElement]
    ) -> float:
        """Estimate reading time for panel in seconds."""

        total_syllables = sum(elem.estimated_syllables for elem in dialogue_elements)

        if narration:
            total_syllables += self._estimate_syllables(narration.text)

        # Average reading speed: 3-4 syllables per second for manga
        base_time = total_syllables / self.reading_speed

        # Add processing time for dialogue bubbles
        bubble_processing = len(dialogue_elements) * 0.5

        return round(base_time + bubble_processing, 1)

    def analyze_dialogue_quality(
        self, dialogue_content: List[PanelDialogue]
    ) -> Dict[str, Any]:
        """Analyze quality of generated dialogue content."""

        if not dialogue_content:
            return {
                "total_panels": 0,
                "panels_with_dialogue": 0,
                "average_elements_per_panel": 0.0,
                "total_reading_time": 0.0,
                "character_balance": {},
                "dialogue_type_distribution": {},
                "quality_score": 0.0
            }

        # Basic statistics
        total_panels = len(dialogue_content)
        panels_with_dialogue = sum(1 for panel in dialogue_content
                                 if len(panel.dialogue_elements) > 0)

        total_elements = sum(len(panel.dialogue_elements) for panel in dialogue_content)
        avg_elements = total_elements / total_panels if total_panels > 0 else 0.0

        total_reading_time = sum(panel.estimated_reading_time for panel in dialogue_content)

        # Character speaking balance
        character_counts = {}
        for panel in dialogue_content:
            for elem in panel.dialogue_elements:
                speaker = elem.speaker or "Unknown"
                character_counts[speaker] = character_counts.get(speaker, 0) + 1

        # Dialogue type distribution
        type_counts = {}
        for panel in dialogue_content:
            for elem in panel.dialogue_elements:
                type_name = elem.dialogue_type.value
                type_counts[type_name] = type_counts.get(type_name, 0) + 1

        # Calculate quality score
        quality_score = self._calculate_dialogue_quality_score(
            dialogue_content, panels_with_dialogue, total_panels
        )

        return {
            "total_panels": total_panels,
            "panels_with_dialogue": panels_with_dialogue,
            "average_elements_per_panel": round(avg_elements, 1),
            "total_reading_time": round(total_reading_time, 1),
            "character_balance": character_counts,
            "dialogue_type_distribution": type_counts,
            "quality_score": quality_score
        }

    def _calculate_dialogue_quality_score(
        self, dialogue_content: List[PanelDialogue],
        panels_with_dialogue: int, total_panels: int
    ) -> float:
        """Calculate overall quality score for dialogue content."""

        score = 0.0
        factors = 0

        # Coverage factor (panels with dialogue)
        if total_panels > 0:
            coverage = panels_with_dialogue / total_panels
            score += coverage * 0.3
            factors += 0.3

        # Length distribution factor
        lengths = []
        for panel in dialogue_content:
            for elem in panel.dialogue_elements:
                lengths.append(len(elem.text))

        if lengths:
            # Prefer moderate length dialogues
            avg_length = sum(lengths) / len(lengths)
            if 10 <= avg_length <= 20:  # Ideal range
                score += 0.25
            elif 5 <= avg_length <= 25:  # Acceptable range
                score += 0.15
            factors += 0.25

        # Reading time factor
        reading_times = [panel.estimated_reading_time for panel in dialogue_content]
        if reading_times:
            avg_time = sum(reading_times) / len(reading_times)
            if 2.0 <= avg_time <= 8.0:  # Ideal range
                score += 0.2
            elif 1.0 <= avg_time <= 12.0:  # Acceptable range
                score += 0.1
            factors += 0.2

        # Diversity factor
        unique_types = set()
        for panel in dialogue_content:
            for elem in panel.dialogue_elements:
                unique_types.add(elem.dialogue_type.value)

        if len(unique_types) >= 2:
            score += 0.15
        elif len(unique_types) == 1:
            score += 0.05
        factors += 0.15

        # Consistency factor - check if all panels have reasonable content
        reasonable_panels = sum(1 for panel in dialogue_content
                              if panel.total_text_elements <= 5 and panel.estimated_reading_time <= 15)
        consistency = reasonable_panels / total_panels if total_panels > 0 else 0
        score += consistency * 0.1
        factors += 0.1

        # Normalize score
        final_score = score / factors if factors > 0 else 0.0
        return round(min(1.0, max(0.0, final_score)), 2)