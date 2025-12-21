import pytest
from hyprbind.core.models import BindType


def test_bind_type_enum_values():
    """Test BindType enum has all expected values."""
    assert BindType.BINDD.value == "bindd"
    assert BindType.BIND.value == "bind"
    assert BindType.BINDEL.value == "bindel"
    assert BindType.BINDM.value == "bindm"


from hyprbind.core.models import Binding, BindType


def test_binding_creation():
    """Test creating a Binding instance."""
    binding = Binding(
        type=BindType.BINDD,
        modifiers=["$mainMod"],
        key="Q",
        description="Close window",
        action="killactive",
        params="",
        submap=None,
        line_number=10,
        category="Window Management",
    )

    assert binding.type == BindType.BINDD
    assert binding.modifiers == ["$mainMod"]
    assert binding.key == "Q"
    assert binding.description == "Close window"
    assert binding.action == "killactive"


def test_binding_display_name():
    """Test display_name property formats correctly."""
    binding = Binding(
        type=BindType.BIND,
        modifiers=["$mainMod", "SHIFT"],
        key="Q",
        description="",
        action="exec",
        params="thunar",
        submap=None,
        line_number=1,
        category="Apps",
    )

    assert binding.display_name == "Super + Shift + Q"


def test_binding_display_name_no_modifiers():
    """Test display_name with no modifiers."""
    binding = Binding(
        type=BindType.BIND,
        modifiers=[],
        key="XF86AudioPlay",
        description="",
        action="exec",
        params="playerctl play-pause",
        submap=None,
        line_number=1,
        category="Media",
    )

    assert binding.display_name == "XF86AudioPlay"


def test_binding_conflicts_with_same_binding():
    """Test conflict detection with identical binding."""
    binding1 = Binding(
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

    binding2 = Binding(
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

    assert binding1.conflicts_with(binding2)


def test_binding_no_conflict_different_key():
    """Test no conflict when keys differ."""
    binding1 = Binding(
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

    binding2 = Binding(
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

    assert not binding1.conflicts_with(binding2)


from hyprbind.core.models import Category, Config


def test_category_creation():
    """Test creating Category."""
    category = Category(name="Window Management", icon="window-symbolic")
    assert category.name == "Window Management"
    assert category.bindings == []
    assert not category.collapsed


def test_config_add_binding():
    """Test adding binding creates category if needed."""
    config = Config()
    binding = Binding(
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

    config.add_binding(binding)

    assert "Window" in config.categories
    assert binding in config.categories["Window"].bindings


def test_config_get_all_bindings():
    """Test retrieving all bindings across categories."""
    config = Config()

    binding1 = Binding(
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

    binding2 = Binding(
        type=BindType.BIND,
        modifiers=["$mainMod"],
        key="1",
        description="",
        action="workspace",
        params="1",
        submap=None,
        line_number=2,
        category="Workspace",
    )

    config.add_binding(binding1)
    config.add_binding(binding2)

    all_bindings = config.get_all_bindings()
    assert len(all_bindings) == 2
    assert binding1 in all_bindings
    assert binding2 in all_bindings


def test_binding_conflict_key():
    """Test conflict_key property generates consistent hash keys."""
    binding = Binding(
        type=BindType.BIND,
        modifiers=["SHIFT", "$mainMod"],  # Note: order varies
        key="Q",
        description="",
        action="killactive",
        params="",
        submap=None,
        line_number=1,
        category="Window",
    )

    # Key should be a tuple of (sorted modifiers tuple, key, submap)
    expected_key = (("$mainMod", "SHIFT"), "Q", None)
    assert binding.conflict_key == expected_key


def test_binding_conflict_key_different_modifier_order():
    """Test conflict_key is same regardless of modifier order."""
    binding1 = Binding(
        type=BindType.BIND,
        modifiers=["SHIFT", "$mainMod"],
        key="Q",
        description="",
        action="exec",
        params="",
        submap=None,
        line_number=1,
        category="Window",
    )

    binding2 = Binding(
        type=BindType.BIND,
        modifiers=["$mainMod", "SHIFT"],  # Different order
        key="Q",
        description="",
        action="killactive",
        params="",
        submap=None,
        line_number=2,
        category="Window",
    )

    assert binding1.conflict_key == binding2.conflict_key


def test_binding_conflict_key_with_submap():
    """Test conflict_key includes submap."""
    binding = Binding(
        type=BindType.BIND,
        modifiers=["$mainMod"],
        key="Q",
        description="",
        action="exec",
        params="",
        submap="resize",
        line_number=1,
        category="Window",
    )

    expected_key = (("$mainMod",), "Q", "resize")
    assert binding.conflict_key == expected_key


def test_config_binding_index_created():
    """Test binding index is maintained when adding bindings."""
    config = Config()
    binding = Binding(
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

    config.add_binding(binding)

    # Index should contain the binding
    assert binding.conflict_key in config._binding_index
    assert config._binding_index[binding.conflict_key] == binding


def test_config_find_conflict_returns_binding():
    """Test find_conflict returns conflicting binding."""
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

    config.add_binding(existing)

    new_binding = Binding(
        type=BindType.BIND,
        modifiers=["$mainMod"],
        key="Q",
        description="",
        action="exec",
        params="other",
        submap=None,
        line_number=2,
        category="Apps",
    )

    conflict = config.find_conflict(new_binding)
    assert conflict == existing


def test_config_find_conflict_returns_none_when_no_conflict():
    """Test find_conflict returns None when no conflict exists."""
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

    config.add_binding(existing)

    new_binding = Binding(
        type=BindType.BIND,
        modifiers=["$mainMod"],
        key="W",  # Different key
        description="",
        action="exec",
        params="other",
        submap=None,
        line_number=2,
        category="Apps",
    )

    conflict = config.find_conflict(new_binding)
    assert conflict is None


def test_config_remove_binding_updates_index():
    """Test removing binding updates the index."""
    config = Config()
    binding = Binding(
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

    config.add_binding(binding)
    assert binding.conflict_key in config._binding_index

    config.remove_binding(binding)
    assert binding.conflict_key not in config._binding_index
