"""Tests for ConfigManager."""

from pathlib import Path

import pytest

from hyprbind.core.config_manager import ConfigManager, OperationResult
from hyprbind.core.models import Binding, BindType


@pytest.fixture
def sample_config_path():
    """Path to sample keybinds config."""
    return Path(__file__).parent.parent / "fixtures" / "sample_keybinds.conf"


@pytest.fixture
def manager(sample_config_path):
    """ConfigManager instance with sample config."""
    return ConfigManager(sample_config_path, skip_validation=True)


class TestLoadConfig:
    """Test config loading."""

    def test_load_config_file(self, manager):
        """Load config from fixture file."""
        config = manager.load()

        assert config is not None
        assert len(config.get_all_bindings()) > 0
        assert "Window Actions" in config.categories
        assert "Workspaces" in config.categories


class TestAddBinding:
    """Test adding bindings."""

    def test_add_binding_no_conflict(self, manager):
        """Add binding successfully when no conflict."""
        manager.load()

        new_binding = Binding(
            type=BindType.BINDD,
            modifiers=["$mainMod"],
            key="F1",
            description="Help window",
            action="exec",
            params="help-app",
            submap=None,
            line_number=0,
            category="Help",
        )

        result = manager.add_binding(new_binding)

        assert result.success is True
        assert result.message == ""
        assert result.conflicts == []
        assert new_binding in manager.config.get_all_bindings()

    def test_add_binding_with_conflict(self, manager):
        """Add conflicting binding returns error with conflicts list."""
        manager.load()

        # Create binding that conflicts with existing one ($mainMod + Q)
        conflicting_binding = Binding(
            type=BindType.BINDD,
            modifiers=["$mainMod"],
            key="Q",
            description="New action",
            action="exec",
            params="something",
            submap=None,
            line_number=0,
            category="Test",
        )

        result = manager.add_binding(conflicting_binding)

        assert result.success is False
        assert "conflict" in result.message.lower()
        assert len(result.conflicts) == 1
        assert result.conflicts[0].description == "Close window"


class TestRemoveBinding:
    """Test removing bindings."""

    def test_remove_binding(self, manager):
        """Remove existing binding."""
        manager.load()

        # Get an existing binding
        bindings = manager.config.get_all_bindings()
        binding_to_remove = bindings[0]

        result = manager.remove_binding(binding_to_remove)

        assert result.success is True
        assert result.message == "Binding removed"
        assert binding_to_remove not in manager.config.get_all_bindings()

    def test_remove_nonexistent_binding(self, manager):
        """Remove non-existent binding fails."""
        manager.load()

        fake_binding = Binding(
            type=BindType.BINDD,
            modifiers=["$mainMod"],
            key="F12",
            description="Fake",
            action="exec",
            params="fake",
            submap=None,
            line_number=0,
            category="Fake",
        )

        result = manager.remove_binding(fake_binding)

        assert result.success is False
        assert "not found" in result.message.lower()


class TestUpdateBinding:
    """Test updating bindings."""

    def test_update_binding(self, manager):
        """Update existing binding."""
        manager.load()

        # Get an existing binding
        old_binding = manager.config.get_all_bindings()[0]

        # Create updated version with different description
        new_binding = Binding(
            type=old_binding.type,
            modifiers=old_binding.modifiers,
            key="F2",  # Different key to avoid conflict
            description="Updated description",
            action=old_binding.action,
            params=old_binding.params,
            submap=old_binding.submap,
            line_number=old_binding.line_number,
            category=old_binding.category,
        )

        result = manager.update_binding(old_binding, new_binding)

        assert result.success is True
        assert result.message == "Binding updated"
        assert old_binding not in manager.config.get_all_bindings()
        assert new_binding in manager.config.get_all_bindings()

    def test_update_binding_with_conflict(self, manager):
        """Update binding fails if new binding conflicts."""
        manager.load()

        bindings = manager.config.get_all_bindings()
        old_binding = bindings[0]
        conflicting_binding = bindings[1]

        # Create new binding that conflicts with another existing binding
        new_binding = Binding(
            type=old_binding.type,
            modifiers=conflicting_binding.modifiers,
            key=conflicting_binding.key,  # Same key/modifiers as another binding
            description="New description",
            action=old_binding.action,
            params=old_binding.params,
            submap=old_binding.submap,
            line_number=old_binding.line_number,
            category=old_binding.category,
        )

        result = manager.update_binding(old_binding, new_binding)

        assert result.success is False
        assert "rolled back" in result.message.lower()
        assert len(result.conflicts) > 0
        # Old binding should still be there (rollback)
        assert old_binding in manager.config.get_all_bindings()


class TestConfigNotLoaded:
    """Test operations fail if config not loaded."""

    def test_add_binding_without_load(self, sample_config_path):
        """Add binding fails if config not loaded."""
        manager = ConfigManager(sample_config_path, skip_validation=True)

        new_binding = Binding(
            type=BindType.BINDD,
            modifiers=["$mainMod"],
            key="F1",
            description="Test",
            action="exec",
            params="test",
            submap=None,
            line_number=0,
            category="Test",
        )

        result = manager.add_binding(new_binding)

        assert result.success is False
        assert "not loaded" in result.message.lower()

    def test_remove_binding_without_load(self, sample_config_path):
        """Remove binding fails if config not loaded."""
        manager = ConfigManager(sample_config_path, skip_validation=True)

        binding = Binding(
            type=BindType.BINDD,
            modifiers=["$mainMod"],
            key="Q",
            description="Test",
            action="exec",
            params="test",
            submap=None,
            line_number=0,
            category="Test",
        )

        result = manager.remove_binding(binding)

        assert result.success is False
        assert "not loaded" in result.message.lower()

    def test_update_binding_without_load(self, sample_config_path):
        """Update binding fails if config not loaded."""
        manager = ConfigManager(sample_config_path, skip_validation=True)

        old_binding = Binding(
            type=BindType.BINDD,
            modifiers=["$mainMod"],
            key="Q",
            description="Test",
            action="exec",
            params="test",
            submap=None,
            line_number=0,
            category="Test",
        )

        new_binding = Binding(
            type=BindType.BINDD,
            modifiers=["$mainMod"],
            key="W",
            description="Test",
            action="exec",
            params="test",
            submap=None,
            line_number=0,
            category="Test",
        )

        result = manager.update_binding(old_binding, new_binding)

        assert result.success is False
        assert "not loaded" in result.message.lower()


class TestDefaultPath:
    """Test ConfigManager default path behavior."""

    def test_default_config_path(self):
        """ConfigManager uses default path when none provided."""
        manager = ConfigManager()
        expected_path = Path.home() / ".config" / "hypr" / "config" / "keybinds.conf"
        assert manager.config_path == expected_path


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_update_nonexistent_binding(self):
        """Update non-existent binding fails gracefully."""
        fixture_path = Path(__file__).parent.parent / "fixtures" / "sample_keybinds.conf"
        manager = ConfigManager(config_path=fixture_path, skip_validation=True)
        manager.load()

        # Create a binding that doesn't exist in the config
        fake_binding = Binding(
            type=BindType.BINDD,
            modifiers=["$mainMod"],
            key="F99",
            description="Fake",
            action="exec",
            params="fake",
            submap=None,
            line_number=999,
            category="Fake",
        )

        new_binding = Binding(
            type=BindType.BINDD,
            modifiers=["$mainMod"],
            key="F100",
            description="New",
            action="exec",
            params="new",
            submap=None,
            line_number=1000,
            category="Fake",
        )

        result = manager.update_binding(fake_binding, new_binding)

        assert result.success is False
        assert "not found" in result.message.lower()
