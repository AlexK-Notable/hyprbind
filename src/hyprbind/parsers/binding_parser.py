"""Parser for Hyprland keybinding syntax."""

import re
from typing import Optional

from hyprbind.core.models import Binding, BindType


class BindingParser:
    """Parse Hyprland keybinding configuration syntax."""

    @staticmethod
    def parse_line(line: str, line_number: int, category: str = "Uncategorized") -> Optional[Binding]:
        """
        Parse a single binding line.

        Args:
            line: Line from keybinds.conf
            line_number: Line number in file
            category: Category name for this binding

        Returns:
            Binding object or None if line is not a binding
        """
        line = line.strip()

        # Skip empty lines and comments
        if not line or line.startswith("#"):
            return None

        # Match binding patterns: bindd = mods, key, desc, action, params
        # Format: bindtype = modifiers, key, [description,] action, params
        if not any(line.startswith(bt) for bt in ["bindd", "bind", "bindel", "bindm"]):
            return None

        # Split on first '='
        if "=" not in line:
            return None

        bind_type_str, rest = line.split("=", 1)
        bind_type_str = bind_type_str.strip()

        # Determine bind type
        try:
            bind_type = BindType(bind_type_str)
        except ValueError:
            return None

        # Parse the rest: modifiers, key, [description,] action, params
        parts = [p.strip() for p in rest.split(",")]

        if len(parts) < 3:
            return None

        # Extract modifiers and key
        modifiers_str = parts[0]
        key = parts[1]

        # Split modifiers
        modifiers = [m.strip() for m in modifiers_str.split()] if modifiers_str else []

        # bindd has description as third field
        if bind_type == BindType.BINDD:
            if len(parts) < 4:
                return None
            description = parts[2]
            action = parts[3]
            params = ",".join(parts[4:]) if len(parts) > 4 else ""
        else:
            # bind, bindel, bindm don't have description
            description = ""
            action = parts[2]
            params = ",".join(parts[3:]) if len(parts) > 3 else ""

        return Binding(
            type=bind_type,
            modifiers=modifiers,
            key=key,
            description=description,
            action=action,
            params=params,
            submap=None,
            line_number=line_number,
            category=category,
        )
