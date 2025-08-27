"""Configuration management module."""

from .settings import Settings, get_settings

# Export the main settings and getter function
settings = get_settings()

__all__ = [
    "Settings",
    "settings", 
    "get_settings"
]