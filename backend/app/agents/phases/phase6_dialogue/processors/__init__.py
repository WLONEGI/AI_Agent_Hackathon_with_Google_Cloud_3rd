"""Processors for Phase 6: Dialogue and Text Placement.

This module contains the core processing components for Phase 6:
- DialogueGenerator: Handles dialogue content generation
- TextFormatter: Handles text placement and formatting
"""

from .dialogue_generator import DialogueGenerator
from .text_formatter import TextFormatter

__all__ = [
    "DialogueGenerator",
    "TextFormatter"
]