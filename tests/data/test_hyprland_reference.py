"""Tests for Hyprland reference data."""

from hyprbind.data.hyprland_reference import HYPRLAND_ACTIONS


def test_reference_data_exists():
    """Reference data is available."""
    assert len(HYPRLAND_ACTIONS) > 0


def test_reference_data_has_minimum_actions():
    """Reference data has at least 20 actions."""
    assert len(HYPRLAND_ACTIONS) >= 20


def test_reference_data_structure():
    """Reference data has correct structure."""
    action = HYPRLAND_ACTIONS[0]

    assert "name" in action
    assert "description" in action
    assert "example" in action
    assert "category" in action


def test_all_actions_have_required_fields():
    """All actions have required fields."""
    for action in HYPRLAND_ACTIONS:
        assert "name" in action and action["name"], "Action must have a name"
        assert "description" in action and action["description"], "Action must have a description"
        assert "example" in action and action["example"], "Action must have an example"
        assert "category" in action and action["category"], "Action must have a category"


def test_reference_includes_common_actions():
    """Reference includes common Hyprland actions."""
    action_names = [a["name"] for a in HYPRLAND_ACTIONS]

    assert "killactive" in action_names
    assert "exec" in action_names
    assert "workspace" in action_names
    assert "movetoworkspace" in action_names
    assert "togglefloating" in action_names
    assert "fullscreen" in action_names
    assert "movefocus" in action_names


def test_categories_are_valid():
    """All categories are from expected set."""
    valid_categories = {
        "System",
        "Window Management",
        "Workspaces",
        "Focus",
        "Groups",
        "Layouts",
        "Monitors",
    }

    for action in HYPRLAND_ACTIONS:
        assert action["category"] in valid_categories, f"Invalid category: {action['category']}"
