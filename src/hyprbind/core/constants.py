"""Centralized constants for HyprBind configuration.

This module provides all magic numbers, configuration values, and validation
constants used throughout the application. Centralizing these values ensures
consistency and makes tuning easy.
"""

__all__ = [
    "BACKUP_KEEP_COUNT",
    "IPC_TIMEOUT_SECONDS",
    "GITHUB_REQUEST_TIMEOUT",
    "VALID_MODIFIERS",
    "VARIABLE_PATTERN",
    "is_valid_modifier",
]

import re
from typing import FrozenSet

# =============================================================================
# Backup Configuration
# =============================================================================

BACKUP_KEEP_COUNT: int = 5
"""Number of backup files to retain per config file."""

# =============================================================================
# Network Timeouts (seconds)
# =============================================================================

IPC_TIMEOUT_SECONDS: float = 5.0
"""Timeout for Hyprland IPC socket operations."""

GITHUB_REQUEST_TIMEOUT: float = 10.0
"""Timeout for GitHub API requests."""

# =============================================================================
# Modifier Validation
# =============================================================================

VALID_MODIFIERS: FrozenSet[str] = frozenset([
    # Standard modifiers
    "SUPER", "SHIFT", "ALT", "CTRL",
    # X11 modifier aliases
    "MOD1", "MOD2", "MOD3", "MOD4", "MOD5",
    # Left/Right specific
    "SUPER_L", "SUPER_R", "SHIFT_L", "SHIFT_R",
    "ALT_L", "ALT_R", "CTRL_L", "CTRL_R",
    # Lock keys
    "CAPS", "LOCK", "CAPSLOCK", "NUMLOCK",
])
"""Set of valid Hyprland modifier names."""

VARIABLE_PATTERN = re.compile(r'^\$\w+$')
"""Pattern matching Hyprland variable references like $mainMod."""


def is_valid_modifier(mod: str) -> bool:
    """Check if a modifier is valid (built-in or variable reference).

    Args:
        mod: Modifier string to validate

    Returns:
        True if the modifier is a known Hyprland modifier or a variable reference

    Examples:
        >>> is_valid_modifier("SUPER")
        True
        >>> is_valid_modifier("$mainMod")
        True
        >>> is_valid_modifier("INVALID")
        False
    """
    return mod.upper() in VALID_MODIFIERS or bool(VARIABLE_PATTERN.match(mod))
