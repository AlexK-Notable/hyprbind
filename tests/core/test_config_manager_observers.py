"""Tests for ConfigManager observer pattern and dirty tracking."""

from pathlib import Path

import pytest

from hyprbind.core.config_manager import ConfigManager
from hyprbind.core.models import Binding, BindType


@pytest.fixture
def sample_config_path():
    """Path to sample keybinds config."""
    return Path(__file__).parent.parent / "fixtures" / "sample_keybinds.conf"


@pytest.fixture
def manager(sample_config_path):
    """ConfigManager with loaded config."""
    mgr = ConfigManager(sample_config_path)
    mgr.load()
    return mgr


class TestObserverPattern:
    """Test observer pattern implementation."""

    def test_can_add_observer(self, manager):
        """Can register observer callback."""
        called = []

        def observer():
            called.append(True)

        manager.add_observer(observer)
        assert len(called) == 0  # Not called yet

    def test_observer_called_on_add_binding(self, manager):
        """Observer is called when binding is added."""
        called = []

        def observer():
            called.append(True)

        manager.add_observer(observer)

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

        manager.add_binding(new_binding)
        assert len(called) == 1

    def test_observer_called_on_remove_binding(self, manager):
        """Observer is called when binding is removed."""
        called = []

        def observer():
            called.append(True)

        manager.add_observer(observer)

        # Get existing binding
        binding = manager.config.get_all_bindings()[0]

        manager.remove_binding(binding)
        assert len(called) == 1

    def test_observer_called_on_update_binding(self, manager):
        """Observer is called when binding is updated."""
        called = []

        def observer():
            called.append(True)

        manager.add_observer(observer)

        # Get existing binding
        old_binding = manager.config.get_all_bindings()[0]

        # Create updated version
        new_binding = Binding(
            type=old_binding.type,
            modifiers=old_binding.modifiers,
            key="F2",  # Different key
            description=old_binding.description,
            action=old_binding.action,
            params=old_binding.params,
            submap=old_binding.submap,
            line_number=old_binding.line_number,
            category=old_binding.category,
        )

        manager.update_binding(old_binding, new_binding)
        assert len(called) >= 1  # Called at least once (may be called twice due to remove+add)

    def test_observer_not_called_on_failed_operation(self, manager):
        """Observer is NOT called when operation fails."""
        called = []

        def observer():
            called.append(True)

        manager.add_observer(observer)

        # Try to add conflicting binding (should fail)
        existing = manager.config.get_all_bindings()[0]
        conflicting = Binding(
            type=BindType.BINDD,
            modifiers=existing.modifiers,
            key=existing.key,  # Same key/mods = conflict
            description="Conflict",
            action="exec",
            params="test",
            submap=None,
            line_number=0,
            category="Test",
        )

        result = manager.add_binding(conflicting)
        assert not result.success
        assert len(called) == 0  # Observer not called on failure

    def test_multiple_observers(self, manager):
        """Multiple observers can be registered."""
        called1 = []
        called2 = []

        def observer1():
            called1.append(True)

        def observer2():
            called2.append(True)

        manager.add_observer(observer1)
        manager.add_observer(observer2)

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

        manager.add_binding(new_binding)
        assert len(called1) == 1
        assert len(called2) == 1

    def test_can_remove_observer(self, manager):
        """Can unregister observer."""
        called = []

        def observer():
            called.append(True)

        manager.add_observer(observer)
        manager.remove_observer(observer)

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

        manager.add_binding(new_binding)
        assert len(called) == 0  # Observer was removed

    def test_observer_exception_doesnt_break_others(self, manager):
        """Exception in one observer doesn't break others."""
        called = []

        def bad_observer():
            raise ValueError("Test error")

        def good_observer():
            called.append(True)

        manager.add_observer(bad_observer)
        manager.add_observer(good_observer)

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

        manager.add_binding(new_binding)
        assert len(called) == 1  # Good observer still called


class TestDirtyTracking:
    """Test dirty state tracking."""

    def test_not_dirty_after_load(self, manager):
        """Config is not dirty after loading."""
        assert not manager.is_dirty()

    def test_dirty_after_add(self, manager):
        """Config is dirty after adding binding."""
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

        manager.add_binding(new_binding)
        assert manager.is_dirty()

    def test_dirty_after_remove(self, manager):
        """Config is dirty after removing binding."""
        binding = manager.config.get_all_bindings()[0]
        manager.remove_binding(binding)
        assert manager.is_dirty()

    def test_dirty_after_update(self, manager):
        """Config is dirty after updating binding."""
        old_binding = manager.config.get_all_bindings()[0]
        new_binding = Binding(
            type=old_binding.type,
            modifiers=old_binding.modifiers,
            key="F2",
            description=old_binding.description,
            action=old_binding.action,
            params=old_binding.params,
            submap=old_binding.submap,
            line_number=old_binding.line_number,
            category=old_binding.category,
        )

        manager.update_binding(old_binding, new_binding)
        assert manager.is_dirty()

    def test_not_dirty_after_failed_operation(self, manager):
        """Config is NOT dirty after failed operation."""
        # Try to add conflicting binding
        existing = manager.config.get_all_bindings()[0]
        conflicting = Binding(
            type=BindType.BINDD,
            modifiers=existing.modifiers,
            key=existing.key,
            description="Conflict",
            action="exec",
            params="test",
            submap=None,
            line_number=0,
            category="Test",
        )

        result = manager.add_binding(conflicting)
        assert not result.success
        assert not manager.is_dirty()  # Still clean after failed add
