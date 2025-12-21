"""Detect keybinding conflicts."""

from typing import List, Optional

from hyprbind.core.models import Binding, Config


class ConflictDetector:
    """Detect conflicts between keybindings.

    Uses O(1) hash-based index lookup for efficient conflict detection.
    """

    @staticmethod
    def check(binding: Binding, config: Config) -> List[Binding]:
        """
        Check if binding conflicts with existing bindings.

        Uses O(1) hash index lookup via config.find_conflict().

        Args:
            binding: New binding to check
            config: Current configuration

        Returns:
            List of conflicting bindings (empty if no conflicts)
        """
        conflict = config.find_conflict(binding)
        return [conflict] if conflict else []

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
        return config.find_conflict(binding) is not None
