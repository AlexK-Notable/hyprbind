"""High-level configuration management for keybindings."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Callable

from hyprbind.core.backup_manager import BackupManager, BackupInfo
from hyprbind.core.conflict_detector import ConflictDetector
from hyprbind.core.config_writer import ConfigWriter
from hyprbind.core.models import Binding, Config
from hyprbind.core.constants import BACKUP_KEEP_COUNT
from hyprbind.core.logging_config import get_logger
from hyprbind.parsers.config_parser import ConfigParser

logger = get_logger(__name__)


@dataclass
class OperationResult:
    """Result of a configuration operation."""

    success: bool
    message: str = ""
    conflicts: List[Binding] = field(default_factory=list)


class ConfigManager:
    """Manage Hyprland keybinding configurations."""

    def __init__(
        self, config_path: Optional[Path] = None, skip_validation: bool = False
    ):
        """
        Initialize ConfigManager.

        Args:
            config_path: Path to keybinds.conf (defaults to ~/.config/hypr/config/keybinds.conf)
            skip_validation: Skip path validation (for testing with tmp paths)
        """
        if config_path is None:
            config_path = Path.home() / ".config" / "hypr" / "config" / "keybinds.conf"

        self.config_path = config_path
        self.config: Optional[Config] = None
        self._observers: List[Callable[[], None]] = []
        self._dirty = False
        self._skip_validation = skip_validation
        self.backup_manager = BackupManager()

    def add_observer(self, callback: Callable[[], None]) -> None:
        """
        Register observer to be notified of config changes.

        Args:
            callback: Function to call when config changes
        """
        if callback not in self._observers:
            self._observers.append(callback)

    def remove_observer(self, callback: Callable[[], None]) -> None:
        """
        Unregister observer.

        Args:
            callback: Function to remove from observers
        """
        if callback in self._observers:
            self._observers.remove(callback)

    def _notify_observers(self) -> None:
        """Notify all observers of config change."""
        for observer in self._observers:
            try:
                observer()
            except Exception as e:
                # Log error but don't break other observers
                logger.warning("Observer error: %s", e)

    def is_dirty(self) -> bool:
        """
        Check if config has unsaved changes.

        Returns:
            True if config has been modified since last load/save
        """
        return self._dirty

    def load(self) -> Config:
        """
        Load configuration from file.

        Returns:
            Loaded Config object
        """
        self.config = ConfigParser.parse_file(
            self.config_path, skip_validation=self._skip_validation
        )
        self._dirty = False
        self._notify_observers()
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
        self._dirty = True
        self._notify_observers()
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

        # Check if binding exists in the appropriate category
        if binding.category not in self.config.categories:
            return OperationResult(success=False, message="Binding not found")

        category = self.config.categories[binding.category]
        if binding not in category.bindings:
            return OperationResult(success=False, message="Binding not found")

        # Use Config.remove_binding() to maintain index
        self.config.remove_binding(binding)
        self._dirty = True
        self._notify_observers()
        return OperationResult(success=True, message="Binding removed")

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

        # Save original dirty state in case we need to rollback
        was_dirty = self._dirty

        # Remove old binding (this sets dirty and notifies)
        remove_result = self.remove_binding(old_binding)
        if not remove_result.success:
            return remove_result

        # Try to add new binding (this sets dirty and notifies)
        add_result = self.add_binding(new_binding)
        if not add_result.success:
            # Rollback: re-add old binding
            self.config.add_binding(old_binding)
            # Restore original dirty state
            self._dirty = was_dirty
            # Notify observers of rollback
            self._notify_observers()
            return OperationResult(
                success=False,
                message=f"Update failed: {add_result.message}. Changes rolled back.",
                conflicts=add_result.conflicts,
            )

        # Success - dirty already set, observers already notified by add_binding
        return OperationResult(success=True, message="Binding updated")

    def save(self, output_path: Optional[Path] = None) -> OperationResult:
        """Save config to file with automatic backup.

        Args:
            output_path: Path to save to (defaults to config_path)

        Returns:
            OperationResult with success status
        """
        if not self.config:
            return OperationResult(
                success=False,
                message="Config not loaded - nothing to save",
            )

        target_path = output_path or self.config_path

        try:
            # Create timestamped backup before writing
            if target_path.exists():
                self.backup_manager.create_backup(
                    target_path, skip_validation=self._skip_validation
                )
                # Also cleanup old backups, keeping last BACKUP_KEEP_COUNT
                self.backup_manager.cleanup_old_backups(target_path, keep=BACKUP_KEEP_COUNT)

            ConfigWriter.write_file(
                self.config, target_path, skip_validation=self._skip_validation
            )
            self._dirty = False
            return OperationResult(
                success=True,
                message=f"Config saved to {target_path}",
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message=f"Failed to save config: {e}",
            )

    def list_backups(self) -> List[BackupInfo]:
        """
        List all available backups for the current config file.

        Returns:
            List of BackupInfo objects, sorted newest first
        """
        return self.backup_manager.list_backups(self.config_path)

    def restore_from_backup(self, backup_info: BackupInfo) -> OperationResult:
        """
        Restore configuration from a backup.

        Args:
            backup_info: BackupInfo object for the backup to restore

        Returns:
            OperationResult with success status
        """
        try:
            # Restore the backup
            self.backup_manager.restore_backup(
                backup_info.path, self.config_path,
                skip_validation=self._skip_validation
            )

            # Reload the config
            self.load()

            return OperationResult(
                success=True,
                message=f"Config restored from backup: {backup_info.timestamp}",
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message=f"Failed to restore backup: {e}",
            )
