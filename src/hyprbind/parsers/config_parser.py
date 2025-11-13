"""Parse complete Hyprland keybinds.conf files."""

import re
from pathlib import Path
from typing import Optional

from hyprbind.core.models import Config, Category
from hyprbind.parsers.binding_parser import BindingParser


class ConfigParser:
    """Parse Hyprland keybindings configuration files."""

    @staticmethod
    def parse_file(file_path: Path) -> Config:
        """
        Parse a keybinds.conf file into a Config object.

        Args:
            file_path: Path to keybinds.conf

        Returns:
            Config object with parsed bindings
        """
        config = Config(file_path=str(file_path))

        if not file_path.exists():
            return config

        with open(file_path, "r") as f:
            content = f.read()
            config.original_content = content

        lines = content.split("\n")
        current_category = "Uncategorized"

        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Detect category from comments
            # Pattern: # ======= Category Name =======
            if stripped.startswith("#") and "=======" in stripped:
                category_match = re.search(r"=+\s+(.+?)\s+=+", stripped)
                if category_match:
                    current_category = category_match.group(1).strip()

            # Parse binding line
            binding = BindingParser.parse_line(line, line_num, current_category)
            if binding:
                config.add_binding(binding)

        return config

    @staticmethod
    def parse_string(content: str) -> Config:
        """
        Parse keybindings from a string.

        Args:
            content: String containing keybindings

        Returns:
            Config object with parsed bindings
        """
        config = Config()
        config.original_content = content

        lines = content.split("\n")
        current_category = "Uncategorized"

        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Detect category from comments
            if stripped.startswith("#") and "=======" in stripped:
                category_match = re.search(r"=+\s+(.+?)\s+=+", stripped)
                if category_match:
                    current_category = category_match.group(1).strip()

            # Parse binding line
            binding = BindingParser.parse_line(line, line_num, current_category)
            if binding:
                config.add_binding(binding)

        return config
