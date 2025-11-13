"""Tests for BackupManager - timestamped backup system."""

import pytest
from pathlib import Path
from datetime import datetime
import time
import tempfile
import shutil

from hyprbind.core.backup_manager import BackupManager, BackupInfo


class TestBackupCreation:
    """Test backup file creation with timestamps."""

    def test_create_backup_generates_timestamped_file(self, tmp_path):
        """Backup filename includes ISO timestamp."""
        config_file = tmp_path / "keybinds.conf"
        config_file.write_text("bind = SUPER, A, exec, app")

        manager = BackupManager(backup_dir=tmp_path / "backups")
        backup_path = manager.create_backup(config_file)

        # Check backup exists
        assert backup_path.exists()

        # Check filename format: keybinds.conf.2025-11-13T14-30-00.backup
        assert backup_path.stem.startswith("keybinds.conf.")
        assert backup_path.suffix == ".backup"

        # Extract timestamp portion
        name_parts = backup_path.stem.split(".")
        assert len(name_parts) == 3  # ['keybinds', 'conf', '2025-11-13T14-30-00']
        timestamp_str = name_parts[2]

        # Verify timestamp format (ISO 8601 compatible)
        assert len(timestamp_str) == 19  # YYYY-MM-DDTHH-MM-SS
        assert timestamp_str[4] == "-"
        assert timestamp_str[7] == "-"
        assert timestamp_str[10] == "T"
        assert timestamp_str[13] == "-"
        assert timestamp_str[16] == "-"

    def test_create_backup_preserves_content(self, tmp_path):
        """Backup contains exact copy of original file."""
        config_file = tmp_path / "keybinds.conf"
        original_content = "bind = SUPER, A, exec, app\nbind = SUPER, B, exec, browser"
        config_file.write_text(original_content)

        manager = BackupManager(backup_dir=tmp_path / "backups")
        backup_path = manager.create_backup(config_file)

        assert backup_path.read_text() == original_content

    def test_create_backup_creates_backup_dir_if_missing(self, tmp_path):
        """Backup directory is created automatically."""
        config_file = tmp_path / "keybinds.conf"
        config_file.write_text("bind = SUPER, A, exec, app")

        backup_dir = tmp_path / "nested" / "backups"
        assert not backup_dir.exists()

        manager = BackupManager(backup_dir=backup_dir)
        backup_path = manager.create_backup(config_file)

        assert backup_dir.exists()
        assert backup_path.exists()
        assert backup_path.parent == backup_dir

    def test_create_backup_nonexistent_file_raises_error(self, tmp_path):
        """Creating backup of non-existent file raises FileNotFoundError."""
        manager = BackupManager(backup_dir=tmp_path / "backups")

        with pytest.raises(FileNotFoundError):
            manager.create_backup(tmp_path / "nonexistent.conf")

    def test_multiple_backups_have_different_timestamps(self, tmp_path):
        """Sequential backups get different timestamps."""
        config_file = tmp_path / "keybinds.conf"
        config_file.write_text("bind = SUPER, A, exec, app")

        manager = BackupManager(backup_dir=tmp_path / "backups")

        backup1 = manager.create_backup(config_file)
        time.sleep(1.1)  # Ensure different second
        backup2 = manager.create_backup(config_file)

        assert backup1 != backup2
        assert backup1.exists()
        assert backup2.exists()


class TestListBackups:
    """Test listing available backups for a config file."""

    def test_list_backups_returns_empty_for_no_backups(self, tmp_path):
        """No backups returns empty list."""
        config_file = tmp_path / "keybinds.conf"
        manager = BackupManager(backup_dir=tmp_path / "backups")

        backups = manager.list_backups(config_file)

        assert backups == []

    def test_list_backups_finds_timestamped_backups(self, tmp_path):
        """List finds all backups for a config file."""
        config_file = tmp_path / "keybinds.conf"
        config_file.write_text("original")

        manager = BackupManager(backup_dir=tmp_path / "backups")

        # Create 3 backups
        backup1 = manager.create_backup(config_file)
        time.sleep(1.1)
        backup2 = manager.create_backup(config_file)
        time.sleep(1.1)
        backup3 = manager.create_backup(config_file)

        backups = manager.list_backups(config_file)

        assert len(backups) == 3
        # Should be sorted newest first
        assert backups[0].path == backup3
        assert backups[1].path == backup2
        assert backups[2].path == backup1

    def test_list_backups_includes_metadata(self, tmp_path):
        """Backup info includes timestamp, size, and path."""
        config_file = tmp_path / "keybinds.conf"
        content = "bind = SUPER, A, exec, app"
        config_file.write_text(content)

        manager = BackupManager(backup_dir=tmp_path / "backups")
        backup_path = manager.create_backup(config_file)

        backups = manager.list_backups(config_file)

        assert len(backups) == 1
        backup_info = backups[0]

        assert isinstance(backup_info, BackupInfo)
        assert backup_info.path == backup_path
        assert backup_info.size == len(content)
        assert isinstance(backup_info.timestamp, datetime)
        assert backup_info.original_name == "keybinds.conf"

    def test_list_backups_only_returns_matching_file(self, tmp_path):
        """List only returns backups for the specific config file."""
        config1 = tmp_path / "keybinds.conf"
        config2 = tmp_path / "monitors.conf"
        config1.write_text("bind1")
        config2.write_text("monitor1")

        manager = BackupManager(backup_dir=tmp_path / "backups")

        backup1 = manager.create_backup(config1)
        backup2 = manager.create_backup(config2)

        keybind_backups = manager.list_backups(config1)
        monitor_backups = manager.list_backups(config2)

        assert len(keybind_backups) == 1
        assert len(monitor_backups) == 1
        assert keybind_backups[0].path == backup1
        assert monitor_backups[0].path == backup2

    def test_list_backups_ignores_non_backup_files(self, tmp_path):
        """List ignores files without .backup extension."""
        config_file = tmp_path / "keybinds.conf"
        config_file.write_text("bind")

        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()

        manager = BackupManager(backup_dir=backup_dir)

        # Create real backup
        real_backup = manager.create_backup(config_file)

        # Create fake files that should be ignored
        (backup_dir / "keybinds.conf.txt").write_text("not a backup")
        (backup_dir / "other.conf.2025-11-13T14-30-00.backup").write_text("wrong file")
        (backup_dir / "keybinds.conf.backup").write_text("no timestamp")

        backups = manager.list_backups(config_file)

        assert len(backups) == 1
        assert backups[0].path == real_backup


class TestRestoreBackup:
    """Test restoring from backup."""

    def test_restore_backup_replaces_target_file(self, tmp_path):
        """Restore overwrites target with backup content."""
        config_file = tmp_path / "keybinds.conf"
        config_file.write_text("original content")

        manager = BackupManager(backup_dir=tmp_path / "backups")
        backup_path = manager.create_backup(config_file)

        # Modify original
        config_file.write_text("modified content")

        # Restore
        manager.restore_backup(backup_path, config_file)

        assert config_file.read_text() == "original content"

    def test_restore_backup_creates_target_if_missing(self, tmp_path):
        """Restore creates target file if it doesn't exist."""
        config_file = tmp_path / "keybinds.conf"
        config_file.write_text("content")

        manager = BackupManager(backup_dir=tmp_path / "backups")
        backup_path = manager.create_backup(config_file)

        # Delete original
        config_file.unlink()
        assert not config_file.exists()

        # Restore
        manager.restore_backup(backup_path, config_file)

        assert config_file.exists()
        assert config_file.read_text() == "content"

    def test_restore_backup_nonexistent_backup_raises_error(self, tmp_path):
        """Restoring non-existent backup raises FileNotFoundError."""
        manager = BackupManager(backup_dir=tmp_path / "backups")

        with pytest.raises(FileNotFoundError):
            manager.restore_backup(
                tmp_path / "backups" / "fake.backup", tmp_path / "target.conf"
            )

    def test_restore_backup_creates_target_dir_if_needed(self, tmp_path):
        """Restore creates target directory structure."""
        config_file = tmp_path / "keybinds.conf"
        config_file.write_text("content")

        manager = BackupManager(backup_dir=tmp_path / "backups")
        backup_path = manager.create_backup(config_file)

        # Restore to new location
        new_location = tmp_path / "new" / "nested" / "keybinds.conf"
        assert not new_location.parent.exists()

        manager.restore_backup(backup_path, new_location)

        assert new_location.exists()
        assert new_location.read_text() == "content"


class TestCleanupOldBackups:
    """Test automatic cleanup of old backups."""

    def test_cleanup_keeps_n_most_recent_backups(self, tmp_path):
        """Cleanup retains only the N newest backups."""
        config_file = tmp_path / "keybinds.conf"
        config_file.write_text("content")

        manager = BackupManager(backup_dir=tmp_path / "backups")

        # Create 5 backups
        backups = []
        for i in range(5):
            backup = manager.create_backup(config_file)
            backups.append(backup)
            time.sleep(1.1)

        # Keep only 3 most recent
        deleted_count = manager.cleanup_old_backups(config_file, keep=3)

        assert deleted_count == 2

        # Check which backups remain
        remaining = manager.list_backups(config_file)
        assert len(remaining) == 3

        # Should keep the 3 newest (last created)
        assert backups[4].exists()  # newest
        assert backups[3].exists()
        assert backups[2].exists()
        assert not backups[1].exists()  # deleted
        assert not backups[0].exists()  # deleted

    def test_cleanup_with_fewer_backups_than_keep_limit(self, tmp_path):
        """Cleanup does nothing if backups < keep limit."""
        config_file = tmp_path / "keybinds.conf"
        config_file.write_text("content")

        manager = BackupManager(backup_dir=tmp_path / "backups")

        # Create only 2 backups
        backup1 = manager.create_backup(config_file)
        time.sleep(1.1)
        backup2 = manager.create_backup(config_file)

        # Try to keep 5
        deleted_count = manager.cleanup_old_backups(config_file, keep=5)

        assert deleted_count == 0
        assert backup1.exists()
        assert backup2.exists()

    def test_cleanup_with_no_backups(self, tmp_path):
        """Cleanup handles no backups gracefully."""
        config_file = tmp_path / "keybinds.conf"
        manager = BackupManager(backup_dir=tmp_path / "backups")

        deleted_count = manager.cleanup_old_backups(config_file, keep=5)

        assert deleted_count == 0

    def test_cleanup_only_affects_specified_config(self, tmp_path):
        """Cleanup only removes backups for the specified file."""
        config1 = tmp_path / "keybinds.conf"
        config2 = tmp_path / "monitors.conf"
        config1.write_text("bind1")
        config2.write_text("monitor1")

        manager = BackupManager(backup_dir=tmp_path / "backups")

        # Create multiple backups for both configs
        keybind_backups = []
        monitor_backups = []

        for i in range(5):
            keybind_backups.append(manager.create_backup(config1))
            monitor_backups.append(manager.create_backup(config2))
            time.sleep(1.1)

        # Cleanup only keybinds, keep 2
        deleted = manager.cleanup_old_backups(config1, keep=2)

        assert deleted == 3

        # Check keybind backups
        remaining_keybinds = manager.list_backups(config1)
        assert len(remaining_keybinds) == 2

        # Monitor backups should be untouched
        remaining_monitors = manager.list_backups(config2)
        assert len(remaining_monitors) == 5


class TestBackupManagerDefaultBehavior:
    """Test default BackupManager configuration."""

    def test_default_backup_dir_is_config_dir(self, tmp_path):
        """Default backup directory is in same dir as config."""
        # Create manager without backup_dir
        manager = BackupManager()

        # Should use default
        expected = Path.home() / ".config" / "hypr" / "config" / ".backups"
        assert manager.backup_dir == expected

    def test_custom_backup_dir_is_used(self, tmp_path):
        """Custom backup directory is respected."""
        custom_dir = tmp_path / "my_backups"
        manager = BackupManager(backup_dir=custom_dir)

        assert manager.backup_dir == custom_dir
