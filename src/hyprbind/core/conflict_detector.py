"""Detect keybinding conflicts."""

from typing import List

from hyprbind.core.models import Binding, Config


class ConflictDetector:
    """Detect conflicts between keybindings."""

    @staticmethod
    def check(binding: Binding, config: Config) -> List[Binding]:
        """
        Check if binding conflicts with existing bindings.

        Args:
            binding: New binding to check
            config: Current configuration

        Returns:
            List of conflicting bindings (empty if no conflicts)
        """
        conflicts = []

        for existing in config.get_all_bindings():
            if binding.conflicts_with(existing):
                conflicts.append(existing)

        return conflicts

    @staticmethod
    def has_conflicts(binding: Binding, config: Config) -> bool:
        """
        Quick check if binding has any conflicts.

        Args:
            binding: New binding to check
            config: Current configuration

        Returns:
            True if conflicts exist
        """
        return len(ConflictDetector.check(binding, config)) > 0
