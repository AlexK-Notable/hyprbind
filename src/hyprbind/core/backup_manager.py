"""Backup system for configuration files with timestamping and restore functionality."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import shutil

from hyprbind.core.logging_config import get_logger
from hyprbind.core.validators import PathValidator
from hyprbind.core.constants import BACKUP_KEEP_COUNT

logger = get_logger(__name__)


@dataclass
class BackupInfo:
    """Information about a backup file."""

    path: Path
    timestamp: datetime
    size: int
    original_name: str


class BackupManager:
    """Manages timestamped backups of configuration files."""

    def __init__(self, backup_dir: Path | None = None):
        """
        Initialize BackupManager.

        Args:
            backup_dir: Directory to store backups (defaults to ~/.config/hypr/config/.backups)
        """
        if backup_dir is None:
            backup_dir = (
                Path.home() / ".config" / "hypr" / "config" / ".backups"
            )

        self.backup_dir = backup_dir

    def create_backup(
        self, config_path: Path, skip_validation: bool = False
    ) -> Path:
        """
        Create a timestamped backup of a config file.

        Args:
            config_path: Path to config file to backup
            skip_validation: Skip path validation (for testing)

        Returns:
            Path to created backup file

        Raises:
            ValueError: If path fails security validation
            FileNotFoundError: If config_path doesn't exist
        """
        # Validate source path
        if not skip_validation:
            path_error = PathValidator.validate_local_path(config_path)
            if path_error:
                logger.warning("Backup source path validation failed: %s (%s)", config_path, path_error)
                raise ValueError(path_error)

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Generate timestamped filename
        # Format: keybinds.conf.2025-11-13T14-30-00.backup
        timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        backup_name = f"{config_path.name}.{timestamp}.backup"
        backup_path = self.backup_dir / backup_name

        # Copy file to backup location
        shutil.copy2(config_path, backup_path)

        return backup_path

    def list_backups(self, config_path: Path) -> List[BackupInfo]:
        """
        List all backups for a specific config file.

        Args:
            config_path: Path to config file

        Returns:
            List of BackupInfo objects, sorted newest first
        """
        if not self.backup_dir.exists():
            return []

        config_name = config_path.name
        backups = []

        # Find all backup files matching this config
        # Pattern: keybinds.conf.YYYY-MM-DDTHH-MM-SS.backup
        for backup_file in self.backup_dir.glob(f"{config_name}.*.backup"):
            # Validate filename format
            parts = backup_file.stem.split(".")
            if len(parts) < 3:
                continue  # Invalid format, skip

            # Extract timestamp portion (last part before .backup)
            timestamp_str = parts[-1]

            # Verify it looks like a timestamp (19 chars, YYYY-MM-DDTHH-MM-SS)
            if len(timestamp_str) != 19:
                continue

            # Parse timestamp
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H-%M-%S")
            except ValueError:
                continue  # Invalid timestamp format, skip

            # Get file size
            size = backup_file.stat().st_size

            backups.append(
                BackupInfo(
                    path=backup_file,
                    timestamp=timestamp,
                    size=size,
                    original_name=config_name,
                )
            )

        # Sort by timestamp, newest first
        backups.sort(key=lambda b: b.timestamp, reverse=True)

        return backups

    def restore_backup(
        self, backup_path: Path, target_path: Path, skip_validation: bool = False
    ) -> None:
        """
        Restore a backup to the target location.

        Args:
            backup_path: Path to backup file
            target_path: Path where file should be restored
            skip_validation: Skip path validation (for testing)

        Raises:
            ValueError: If target path fails security validation
            FileNotFoundError: If backup_path doesn't exist
        """
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        # Validate target path before restoring
        if not skip_validation:
            path_error = PathValidator.validate_write_path(target_path)
            if path_error:
                logger.warning("Restore target path validation failed: %s (%s)", target_path, path_error)
                raise ValueError(path_error)

        # Ensure target directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy backup to target location
        shutil.copy2(backup_path, target_path)

    def cleanup_old_backups(self, config_path: Path, keep: int = BACKUP_KEEP_COUNT) -> int:
        """
        Delete old backups, keeping only the N most recent.

        Args:
            config_path: Path to config file
            keep: Number of backups to keep (default: BACKUP_KEEP_COUNT)

        Returns:
            Number of backups deleted
        """
        backups = self.list_backups(config_path)

        if len(backups) <= keep:
            return 0

        # Delete oldest backups (backups is sorted newest first)
        backups_to_delete = backups[keep:]
        deleted_count = 0

        for backup_info in backups_to_delete:
            try:
                backup_info.path.unlink()
                deleted_count += 1
            except Exception:
                # Continue even if deletion fails
                pass

        return deleted_count
