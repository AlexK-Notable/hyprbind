"""Resolve variable references in Hyprland config."""

import re
from pathlib import Path
from typing import Dict


class VariableResolver:
    """Resolve $variable references in configuration."""

    @staticmethod
    def load_from_file(file_path: Path) -> Dict[str, str]:
        """
        Load variables from a config file.

        Args:
            file_path: Path to config file with variable definitions

        Returns:
            Dictionary mapping variable names to values
        """
        variables = {}

        if not file_path.exists():
            return variables

        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue

                # Match variable assignment: $name = value
                if "=" in line and line.startswith("$"):
                    var_name, value = line.split("=", 1)
                    variables[var_name.strip()] = value.strip()

        return variables

    @staticmethod
    def resolve(text: str, variables: Dict[str, str]) -> str:
        """
        Resolve all $variables in text.

        Args:
            text: Text containing $variable references
            variables: Dictionary of variable mappings

        Returns:
            Text with variables replaced by their values
        """
        result = text

        # Replace all variables
        for var_name, value in variables.items():
            result = result.replace(var_name, value)

        return result

    @staticmethod
    def load_all_variables(config_dir: Path) -> Dict[str, str]:
        """
        Load variables from all standard config files.

        Args:
            config_dir: Path to Hyprland config directory

        Returns:
            Combined dictionary of all variables
        """
        variables = {}

        # Load from variables.conf
        variables_file = config_dir / "variables.conf"
        if variables_file.exists():
            variables.update(VariableResolver.load_from_file(variables_file))

        # Load from defaults.conf
        defaults_file = config_dir / "defaults.conf"
        if defaults_file.exists():
            variables.update(VariableResolver.load_from_file(defaults_file))

        return variables
