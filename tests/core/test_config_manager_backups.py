"""Tests for ConfigManager backup integration."""

import pytest
from pathlib import Path
import time

from hyprbind.core.config_manager import ConfigManager
from hyprbind.core.models import Binding, BindType


class TestConfigManagerBackupIntegration:
    """Test automatic backup creation and management via ConfigManager."""

    def test_save_creates_timestamped_backup(self, tmp_path):
        """Saving config creates timestamped backup automatically."""
        config_file = tmp_path / "keybinds.conf"
        config_file.write_text("bind = SUPER, A, exec, app")

        manager = ConfigManager(config_path=config_file, skip_validation=True)
        # Use isolated backup directory for this test
        from hyprbind.core.backup_manager import BackupManager
        manager.backup_manager = BackupManager(backup_dir=tmp_path / "backups")

        manager.load()

        # Save should create backup
        result = manager.save()

        assert result.success
        backups = manager.list_backups()
        assert len(backups) == 1
        assert backups[0].path.suffix == ".backup"

    def test_save_does_not_create_backup_for_new_file(self, tmp_path):
        """No backup created when saving to new file."""
        config_file = tmp_path / "keybinds.conf"

        manager = ConfigManager(config_path=config_file, skip_validation=True)
        # Use isolated backup directory for this test
        from hyprbind.core.backup_manager import BackupManager
        manager.backup_manager = BackupManager(backup_dir=tmp_path / "backups")

        manager.config = manager.load() if config_file.exists() else None

        # Create minimal config
        from hyprbind.core.models import Config, Category

        manager.config = Config(categories={"Test": Category(name="Test", bindings=[])})

        # Save to new file (doesn't exist yet)
        result = manager.save()

        assert result.success
        # No backup should be created for new file
        backups = manager.list_backups()
        assert len(backups) == 0

    def test_multiple_saves_create_multiple_backups(self, tmp_path):
        """Multiple saves create multiple timestamped backups."""
        config_file = tmp_path / "keybinds.conf"
        config_file.write_text("bind = SUPER, A, exec, app")

        manager = ConfigManager(config_path=config_file, skip_validation=True)
        # Use isolated backup directory for this test
        from hyprbind.core.backup_manager import BackupManager
        manager.backup_manager = BackupManager(backup_dir=tmp_path / "backups")

        manager.load()

        # First save
        manager.save()
        time.sleep(1.1)

        # Second save
        manager.save()
        time.sleep(1.1)

        # Third save
        manager.save()

        backups = manager.list_backups()
        assert len(backups) == 3

        # All should have different timestamps
        timestamps = [b.timestamp for b in backups]
        assert len(timestamps) == len(set(timestamps))

    def test_old_backups_cleaned_up_automatically(self, tmp_path):
        """Old backups are automatically cleaned up, keeping last 5."""
        config_file = tmp_path / "keybinds.conf"
        config_file.write_text("bind = SUPER, A, exec, app")

        manager = ConfigManager(config_path=config_file, skip_validation=True)
        # Use isolated backup directory for this test
        from hyprbind.core.backup_manager import BackupManager
        manager.backup_manager = BackupManager(backup_dir=tmp_path / "backups")

        manager.load()

        # Create 7 backups
        for i in range(7):
            manager.save()
            time.sleep(1.1)

        # Should only have 5 backups (last 5 kept)
        backups = manager.list_backups()
        assert len(backups) == 5

    def test_list_backups_returns_sorted_newest_first(self, tmp_path):
        """Backup list is sorted with newest first."""
        config_file = tmp_path / "keybinds.conf"
        config_file.write_text("bind = SUPER, A, exec, app")

        manager = ConfigManager(config_path=config_file, skip_validation=True)
        # Use isolated backup directory for this test
        from hyprbind.core.backup_manager import BackupManager
        manager.backup_manager = BackupManager(backup_dir=tmp_path / "backups")

        manager.load()

        # Create 3 backups
        for i in range(3):
            manager.save()
            time.sleep(1.1)

        backups = manager.list_backups()

        # Verify sorted newest first
        for i in range(len(backups) - 1):
            assert backups[i].timestamp > backups[i + 1].timestamp


class TestConfigManagerBackupRestore:
    """Test backup restore functionality."""

    def test_restore_from_backup(self, tmp_path):
        """Can restore config from backup."""
        config_file = tmp_path / "keybinds.conf"
        config_file.write_text("bind = SUPER, A, exec, app")

        manager = ConfigManager(config_path=config_file, skip_validation=True)
        # Use isolated backup directory for this test
        from hyprbind.core.backup_manager import BackupManager
        manager.backup_manager = BackupManager(backup_dir=tmp_path / "backups")

        manager.load()

        # Save to create backup
        original_bindings_count = len(manager.config.get_all_bindings())
        manager.save()

        # Get the backup
        backups = manager.list_backups()
        assert len(backups) == 1
        backup_to_restore = backups[0]

        # Modify config
        new_binding = Binding(
            type=BindType.BIND,
            modifiers=["SUPER"],
            key="B",
            action="exec",
            params="browser",
            description="Open browser",
            submap=None,
            line_number=999,
            category="Test",
        )
        manager.add_binding(new_binding)
        manager.save()
        time.sleep(1.1)

        # Config should now have more bindings
        assert len(manager.config.get_all_bindings()) > original_bindings_count

        # Restore from backup
        result = manager.restore_from_backup(backup_to_restore)

        assert result.success
        assert "restored" in result.message.lower()

        # Config should be back to original state
        assert len(manager.config.get_all_bindings()) == original_bindings_count

    def test_restore_reloads_config(self, tmp_path):
        """Restore automatically reloads config from restored file."""
        config_file = tmp_path / "keybinds.conf"
        config_file.write_text("bind = SUPER, A, exec, original")

        manager = ConfigManager(config_path=config_file, skip_validation=True)
        # Use isolated backup directory for this test
        from hyprbind.core.backup_manager import BackupManager
        manager.backup_manager = BackupManager(backup_dir=tmp_path / "backups")

        manager.load()
        manager.save()

        backups = manager.list_backups()
        backup_to_restore = backups[0]

        # Manually modify file
        config_file.write_text("bind = SUPER, A, exec, modified")
        manager.load()

        # Check it's modified
        first_binding = manager.config.get_all_bindings()[0]
        assert first_binding.params == "modified"

        # Restore
        manager.restore_from_backup(backup_to_restore)

        # Should be back to original
        first_binding = manager.config.get_all_bindings()[0]
        assert first_binding.params == "original"

    def test_restore_nonexistent_backup_fails(self, tmp_path):
        """Restoring non-existent backup returns error."""
        config_file = tmp_path / "keybinds.conf"
        config_file.write_text("bind = SUPER, A, exec, app")

        manager = ConfigManager(config_path=config_file, skip_validation=True)
        # Use isolated backup directory for this test
        from hyprbind.core.backup_manager import BackupManager
        manager.backup_manager = BackupManager(backup_dir=tmp_path / "backups")

        manager.load()

        # Create fake backup info
        from hyprbind.core.backup_manager import BackupInfo
        from datetime import datetime

        fake_backup = BackupInfo(
            path=tmp_path / "nonexistent.backup",
            timestamp=datetime.now(),
            size=100,
            original_name="keybinds.conf",
        )

        result = manager.restore_from_backup(fake_backup)

        assert not result.success
        assert "failed" in result.message.lower()


class TestBackupManagerInstance:
    """Test BackupManager instance is properly configured."""

    def test_config_manager_has_backup_manager(self, tmp_path):
        """ConfigManager has BackupManager instance."""
        manager = ConfigManager(config_path=tmp_path / "keybinds.conf", skip_validation=True)

        assert hasattr(manager, "backup_manager")
        assert manager.backup_manager is not None

    def test_backup_manager_uses_default_backup_dir(self, tmp_path):
        """BackupManager uses default .backups directory."""
        manager = ConfigManager(config_path=tmp_path / "keybinds.conf", skip_validation=True)

        expected_dir = Path.home() / ".config" / "hypr" / "config" / ".backups"
        assert manager.backup_manager.backup_dir == expected_dir
