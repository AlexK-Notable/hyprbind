"""Markdown generator for keybinding cheatsheets."""

from datetime import datetime
from typing import List

from hyprbind.core.models import Config, Binding


class MarkdownGenerator:
    """Generate Markdown formatted keybinding cheatsheets."""

    def __init__(self, config: Config) -> None:
        """
        Initialize Markdown generator.

        Args:
            config: Hyprland configuration with keybindings
        """
        self.config = config

    def generate(self) -> str:
        """
        Generate complete Markdown document.

        Returns:
            Markdown formatted string
        """
        lines = []

        # Header
        lines.append("# Hyprland Keybindings")
        lines.append("")

        # Metadata
        lines.extend(self._generate_metadata())
        lines.append("")

        # Bindings grouped by category
        categories = sorted(self.config.categories.keys())
        for category_name in categories:
            category = self.config.categories[category_name]
            if category.bindings:
                lines.append(f"## {category_name}")
                lines.append("")

                for binding in category.bindings:
                    lines.append(self._format_binding(binding))

                lines.append("")

        return "\n".join(lines)

    def _generate_metadata(self) -> List[str]:
        """
        Generate metadata section.

        Returns:
            List of metadata lines
        """
        lines = []
        now = datetime.now()
        lines.append(f"**Generated:** {now.strftime('%Y-%m-%d %H:%M:%S')}")

        if self.config.file_path:
            lines.append(f"**Config:** `{self.config.file_path}`")

        return lines

    def _format_binding(self, binding: Binding) -> str:
        """
        Format a single binding as Markdown list item.

        Args:
            binding: Binding to format

        Returns:
            Markdown formatted binding
        """
        # Get display name (e.g., "Super + Q")
        key_combo = binding.display_name

        # Format description and action
        desc = binding.description or "No description"

        # Include action and params if available
        action_info = binding.action
        if binding.params:
            action_info = f"{binding.action}, {binding.params}"

        return f"- `{key_combo}` - {desc} ({action_info})"
