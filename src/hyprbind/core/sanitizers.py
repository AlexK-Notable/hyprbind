"""Input sanitization for IPC command safety.

This module provides sanitization functions to prevent IPC command injection
when sending binding commands to Hyprland via Unix socket.

Security Considerations:
    - Control characters could disrupt protocol parsing
    - Null bytes could terminate strings early
    - Newlines could inject additional commands

The sanitizer removes these dangerous characters while preserving
legitimate Unicode content (e.g., emoji in descriptions).
"""

__all__ = ["IPCSanitizer"]

import re
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Binding

# Control characters that could disrupt IPC protocol
# Matches ASCII control chars 0x00-0x1F and DEL (0x7F)
CONTROL_CHARS = re.compile(r'[\x00-\x1f\x7f]')


class IPCSanitizer:
    """Sanitize binding fields before IPC command construction.

    This class provides methods to either:
    - sanitize(): Remove dangerous characters (for automatic cleanup)
    - validate(): Check for dangerous characters (for user feedback)

    Example:
        >>> IPCSanitizer.sanitize("hello\\x00world")
        'helloworld'
        >>> IPCSanitizer.validate("bad\\ninput", "Key")
        'Key contains invalid control characters'
    """

    @classmethod
    def sanitize(cls, value: str) -> str:
        """Remove dangerous characters from a string.

        This removes ASCII control characters (0x00-0x1F, 0x7F) but
        preserves valid Unicode including emoji.

        Args:
            value: Raw user input

        Returns:
            Sanitized string safe for IPC commands
        """
        return CONTROL_CHARS.sub('', value)

    @classmethod
    def validate(cls, value: str, field_name: str) -> Optional[str]:
        """Check if value contains dangerous characters.

        Use this when you want to reject invalid input rather than
        silently sanitize it.

        Args:
            value: String to validate
            field_name: Name of field for error message

        Returns:
            Error message if invalid, None if valid
        """
        if CONTROL_CHARS.search(value):
            return f"{field_name} contains invalid control characters"
        return None

    @classmethod
    def validate_binding(cls, binding: 'Binding') -> Optional[str]:
        """Validate all fields of a Binding object.

        Checks key, action, params, description, and all modifiers
        for dangerous characters.

        Args:
            binding: Binding object to validate

        Returns:
            First error found, or None if all fields are valid
        """
        # Check main fields
        checks = [
            (binding.key, "Key"),
            (binding.action, "Action"),
        ]

        # Optional fields - only check if present
        if binding.params:
            checks.append((binding.params, "Parameters"))
        if binding.description:
            checks.append((binding.description, "Description"))

        for value, name in checks:
            error = cls.validate(value, name)
            if error:
                return error

        # Check modifiers
        for mod in binding.modifiers:
            error = cls.validate(mod, "Modifier")
            if error:
                return error

        return None
