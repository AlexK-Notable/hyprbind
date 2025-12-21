"""Tests for conflict detector."""

import pytest
from hyprbind.core.conflict_detector import ConflictDetector
from hyprbind.core.models import Binding, BindType, Config


def test_detect_exact_conflict():
    """Test detecting exact keybinding conflict."""
    config = Config()

    existing = Binding(
        type=BindType.BIND,
        modifiers=["$mainMod"],
        key="Q",
        description="",
        action="killactive",
        params="",
        submap=None,
        line_number=1,
        category="Window",
    )

    new_binding = Binding(
        type=BindType.BIND,
        modifiers=["$mainMod"],
        key="Q",
        description="",
        action="exec",
        params="close-all.sh",
        submap=None,
        line_number=2,
        category="Window",
    )

    config.add_binding(existing)

    conflicts = ConflictDetector.check(new_binding, config)

    assert len(conflicts) == 1
    assert conflicts[0] == existing


def test_no_conflict_different_key():
    """Test no conflict when keys differ."""
    config = Config()

    existing = Binding(
        type=BindType.BIND,
        modifiers=["$mainMod"],
        key="Q",
        description="",
        action="killactive",
        params="",
        submap=None,
        line_number=1,
        category="Window",
    )

    new_binding = Binding(
        type=BindType.BIND,
        modifiers=["$mainMod"],
        key="W",
        description="",
        action="exec",
        params="thunar",
        submap=None,
        line_number=2,
        category="Apps",
    )

    config.add_binding(existing)

    conflicts = ConflictDetector.check(new_binding, config)

    assert len(conflicts) == 0


def test_no_conflict_different_modifiers():
    """Test no conflict when modifiers differ."""
    config = Config()

    existing = Binding(
        type=BindType.BIND,
        modifiers=["$mainMod"],
        key="Q",
        description="",
        action="killactive",
        params="",
        submap=None,
        line_number=1,
        category="Window",
    )

    new_binding = Binding(
        type=BindType.BIND,
        modifiers=["$mainMod", "SHIFT"],
        key="Q",
        description="",
        action="exec",
        params="kill-all.sh",
        submap=None,
        line_number=2,
        category="Window",
    )

    config.add_binding(existing)

    conflicts = ConflictDetector.check(new_binding, config)

    assert len(conflicts) == 0


def test_detect_conflict_with_duplicate_keys_in_config():
    """Test conflict detection when config has duplicate key combos (edge case).

    Note: With O(1) hash index, only one binding is stored per key combo.
    If config already has duplicates (invalid state), we detect the conflict
    with whichever binding was added last. This is correct behavior since
    the primary goal is to prevent NEW conflicts, not audit existing ones.
    """
    config = Config()

    # Add two bindings with same key combination (shouldn't happen in valid config)
    existing1 = Binding(
        type=BindType.BIND,
        modifiers=["$mainMod"],
        key="Q",
        description="",
        action="killactive",
        params="",
        submap=None,
        line_number=1,
        category="Window",
    )

    existing2 = Binding(
        type=BindType.BINDD,
        modifiers=["$mainMod"],
        key="Q",
        description="Close all",
        action="exec",
        params="close-all.sh",
        submap=None,
        line_number=2,
        category="Window",
    )

    new_binding = Binding(
        type=BindType.BIND,
        modifiers=["$mainMod"],
        key="Q",
        description="",
        action="exec",
        params="new-action.sh",
        submap=None,
        line_number=3,
        category="Window",
    )

    config.add_binding(existing1)
    config.add_binding(existing2)  # Overwrites existing1 in index

    conflicts = ConflictDetector.check(new_binding, config)

    # With O(1) index, returns the last-added binding with this key combo
    assert len(conflicts) == 1
    assert conflicts[0] == existing2  # Last one added wins in index


def test_has_conflicts_helper():
    """Test has_conflicts convenience method."""
    config = Config()

    existing = Binding(
        type=BindType.BIND,
        modifiers=["$mainMod"],
        key="Q",
        description="",
        action="killactive",
        params="",
        submap=None,
        line_number=1,
        category="Window",
    )

    new_binding = Binding(
        type=BindType.BIND,
        modifiers=["$mainMod"],
        key="Q",
        description="",
        action="exec",
        params="close-all.sh",
        submap=None,
        line_number=2,
        category="Window",
    )

    config.add_binding(existing)

    assert ConflictDetector.has_conflicts(new_binding, config)


def test_conflict_different_modifier_order():
    """Test conflict detection with modifiers in different order."""
    config = Config()

    existing = Binding(
        type=BindType.BIND,
        modifiers=["$mainMod", "SHIFT"],
        key="Q",
        description="",
        action="killactive",
        params="",
        submap=None,
        line_number=1,
        category="Window",
    )

    new_binding = Binding(
        type=BindType.BIND,
        modifiers=["SHIFT", "$mainMod"],  # Different order
        key="Q",
        description="",
        action="exec",
        params="test.sh",
        submap=None,
        line_number=2,
        category="Window",
    )

    config.add_binding(existing)
    conflicts = ConflictDetector.check(new_binding, config)

    assert len(conflicts) == 1
    assert conflicts[0] == existing


def test_no_conflict_different_submaps():
    """Test bindings in different submaps don't conflict."""
    config = Config()

    global_binding = Binding(
        type=BindType.BIND,
        modifiers=["$mainMod"],
        key="Q",
        description="",
        action="killactive",
        params="",
        submap=None,
        line_number=1,
        category="Window",
    )

    submap_binding = Binding(
        type=BindType.BIND,
        modifiers=["$mainMod"],
        key="Q",
        description="",
        action="exec",
        params="resize.sh",
        submap="resize",
        line_number=2,
        category="Window",
    )

    config.add_binding(global_binding)
    conflicts = ConflictDetector.check(submap_binding, config)

    assert len(conflicts) == 0


def test_conflict_same_submap():
    """Test bindings in same submap do conflict."""
    config = Config()

    binding1 = Binding(
        type=BindType.BIND,
        modifiers=["$mainMod"],
        key="Q",
        description="",
        action="exec",
        params="action1.sh",
        submap="resize",
        line_number=1,
        category="Window",
    )

    binding2 = Binding(
        type=BindType.BIND,
        modifiers=["$mainMod"],
        key="Q",
        description="",
        action="exec",
        params="action2.sh",
        submap="resize",
        line_number=2,
        category="Window",
    )

    config.add_binding(binding1)
    conflicts = ConflictDetector.check(binding2, config)

    assert len(conflicts) == 1
    assert conflicts[0] == binding1


def test_conflict_detector_performance_with_many_bindings():
    """Test ConflictDetector performs well with many bindings (uses O(1) index)."""
    config = Config()

    # Add 100 bindings with different keys
    for i in range(100):
        binding = Binding(
            type=BindType.BIND,
            modifiers=["$mainMod"],
            key=f"F{i}",
            description="",
            action="exec",
            params=f"action{i}",
            submap=None,
            line_number=i,
            category="Test",
        )
        config.add_binding(binding)

    # Check for conflict with the 50th binding
    new_binding = Binding(
        type=BindType.BIND,
        modifiers=["$mainMod"],
        key="F50",  # Conflicts with binding 50
        description="",
        action="exec",
        params="conflict",
        submap=None,
        line_number=101,
        category="Test",
    )

    # Should find conflict efficiently using O(1) index lookup
    conflicts = ConflictDetector.check(new_binding, config)
    assert len(conflicts) == 1
    assert conflicts[0].key == "F50"


def test_conflict_detector_no_conflict_with_many_bindings():
    """Test ConflictDetector returns empty list efficiently with many bindings."""
    config = Config()

    # Add 100 bindings
    for i in range(100):
        binding = Binding(
            type=BindType.BIND,
            modifiers=["$mainMod"],
            key=f"F{i}",
            description="",
            action="exec",
            params=f"action{i}",
            submap=None,
            line_number=i,
            category="Test",
        )
        config.add_binding(binding)

    # Check for non-conflicting binding
    new_binding = Binding(
        type=BindType.BIND,
        modifiers=["$mainMod", "SHIFT"],  # Different modifiers
        key="F50",
        description="",
        action="exec",
        params="no-conflict",
        submap=None,
        line_number=101,
        category="Test",
    )

    conflicts = ConflictDetector.check(new_binding, config)
    assert len(conflicts) == 0
