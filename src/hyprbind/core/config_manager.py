"""High-level configuration management for keybindings."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from hyprbind.core.conflict_detector import ConflictDetector
from hyprbind.core.models import Binding, Config
from hyprbind.parsers.config_parser import ConfigParser


@dataclass
class OperationResult:
    """Result of a configuration operation."""

    success: bool
    message: str = ""
    conflicts: List[Binding] = field(default_factory=list)


class ConfigManager:
    """Manage Hyprland keybinding configurations."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize ConfigManager.

        Args:
            config_path: Path to keybinds.conf (defaults to ~/.config/hypr/config/keybinds.conf)
        """
        if config_path is None:
            config_path = Path.home() / ".config" / "hypr" / "config" / "keybinds.conf"

        self.config_path = config_path
        self.config: Optional[Config] = None

    def load(self) -> Config:
        """
        Load configuration from file.

        Returns:
            Loaded Config object
        """
        self.config = ConfigParser.parse_file(self.config_path)
        return self.config

    def add_binding(self, binding: Binding) -> OperationResult:
        """
        Add a new binding to configuration.

        Args:
            binding: Binding to add

        Returns:
            OperationResult with success status and any conflicts
        """
        if self.config is None:
            return OperationResult(
                success=False, message="Config not loaded. Call load() first."
            )

        # Check for conflicts
        conflicts = ConflictDetector.check(binding, self.config)

        if conflicts:
            return OperationResult(
                success=False,
                message=f"Binding conflicts with {len(conflicts)} existing binding(s)",
                conflicts=conflicts,
            )

        # No conflicts, add binding
        self.config.add_binding(binding)
        return OperationResult(success=True)

    def remove_binding(self, binding: Binding) -> OperationResult:
        """
        Remove a binding from configuration.

        Args:
            binding: Binding to remove

        Returns:
            OperationResult with success status
        """
        if self.config is None:
            return OperationResult(
                success=False, message="Config not loaded. Call load() first."
            )

        # Search through categories to find and remove binding
        for category in self.config.categories.values():
            if binding in category.bindings:
                category.bindings.remove(binding)
                return OperationResult(success=True, message="Binding removed")

        return OperationResult(success=False, message="Binding not found")

    def update_binding(
        self, old_binding: Binding, new_binding: Binding
    ) -> OperationResult:
        """
        Update an existing binding.

        Args:
            old_binding: Binding to replace
            new_binding: New binding

        Returns:
            OperationResult with success status
        """
        if self.config is None:
            return OperationResult(
                success=False, message="Config not loaded. Call load() first."
            )

        # Remove old binding
        remove_result = self.remove_binding(old_binding)
        if not remove_result.success:
            return remove_result

        # Try to add new binding
        add_result = self.add_binding(new_binding)
        if not add_result.success:
            # Rollback: re-add old binding
            self.config.add_binding(old_binding)
            return OperationResult(
                success=False,
                message=f"Update failed: {add_result.message}. Changes rolled back.",
                conflicts=add_result.conflicts,
            )

        return OperationResult(success=True, message="Binding updated")
