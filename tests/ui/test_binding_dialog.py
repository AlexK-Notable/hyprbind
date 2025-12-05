"""Tests for BindingDialog."""

import pytest
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw
from pathlib import Path
from unittest.mock import MagicMock, patch

from hyprbind.core.config_manager import ConfigManager, OperationResult
from hyprbind.core.models import Binding, BindType, Config, Category
from hyprbind.ui.binding_dialog import BindingDialog


@pytest.fixture
def config_manager():
    """Create ConfigManager with test config."""
    manager = ConfigManager()
    manager.config = Config()
    manager.config.categories = {
        "Applications": Category(name="Applications"),
        "Window Management": Category(name="Window Management"),
    }
    # Mock save method (not implemented yet)
    manager.save = MagicMock(return_value=OperationResult(success=True))
    return manager


@pytest.fixture
def sample_binding():
    """Create a sample binding for testing."""
    return Binding(
        type=BindType.BINDD,
        modifiers=["$mainMod", "SHIFT"],
        key="Q",
        description="Close window",
        action="killactive",
        params="",
        submap=None,
        line_number=42,
        category="Window Management",
    )


def test_dialog_creation_add_mode(config_manager, mode_manager):
    """Test dialog creation in add mode (no binding)."""
    dialog = BindingDialog(
        config_manager=config_manager,
        mode_manager=mode_manager
    )

    assert dialog.original_binding is None
    assert isinstance(dialog, Adw.Window)
    assert dialog.config_manager is config_manager


def test_dialog_creation_edit_mode(config_manager, mode_manager, sample_binding):
    """Test dialog creation in edit mode (with binding)."""
    dialog = BindingDialog(
        config_manager=config_manager,
        mode_manager=mode_manager,
        binding=sample_binding
    )

    assert dialog.original_binding == sample_binding
    assert isinstance(dialog, Adw.Window)


def test_form_fields_populated_in_edit_mode(config_manager, mode_manager, sample_binding):
    """Test that form fields are populated when editing a binding."""
    dialog = BindingDialog(
        config_manager=config_manager,
        mode_manager=mode_manager,
        binding=sample_binding
    )

    # Check bind type (0 = bindd)
    assert dialog.type_row.get_selected() == 0

    # Check key
    assert dialog.key_entry.get_text() == "Q"

    # Check modifiers
    assert dialog.modifiers_entry.get_text() == "$mainMod, SHIFT"

    # Check description
    assert dialog.description_entry.get_text() == "Close window"

    # Check action
    assert dialog.action_entry.get_text() == "killactive"

    # Check params (empty in this case)
    assert dialog.params_entry.get_text() == ""


def test_validation_empty_key(config_manager, mode_manager):
    """Test validation fails for empty key."""
    dialog = BindingDialog(
        config_manager=config_manager,
        mode_manager=mode_manager
    )

    dialog.key_entry.set_text("")
    dialog.action_entry.set_text("exec")

    error = dialog._validate_input()
    assert error is not None
    assert "Key cannot be empty" in error


def test_validation_empty_action(config_manager, mode_manager):
    """Test validation fails for empty action."""
    dialog = BindingDialog(
        config_manager=config_manager,
        mode_manager=mode_manager
    )

    dialog.key_entry.set_text("Q")
    dialog.action_entry.set_text("")

    error = dialog._validate_input()
    assert error is not None
    assert "Action cannot be empty" in error


def test_validation_invalid_modifiers(config_manager, mode_manager):
    """Test validation fails for invalid modifiers."""
    dialog = BindingDialog(
        config_manager=config_manager,
        mode_manager=mode_manager
    )

    dialog.key_entry.set_text("Q")
    dialog.action_entry.set_text("exec")
    dialog.modifiers_entry.set_text("INVALID_MOD")

    error = dialog._validate_input()
    assert error is not None
    assert "Invalid modifier" in error


def test_validation_valid_input(config_manager, mode_manager):
    """Test validation passes for valid input."""
    dialog = BindingDialog(
        config_manager=config_manager,
        mode_manager=mode_manager
    )

    dialog.key_entry.set_text("Q")
    dialog.action_entry.set_text("exec")
    dialog.modifiers_entry.set_text("$mainMod, SHIFT")

    error = dialog._validate_input()
    assert error is None


def test_get_binding_new_binding(config_manager, mode_manager):
    """Test get_binding() creates new binding correctly."""
    dialog = BindingDialog(
        config_manager=config_manager,
        mode_manager=mode_manager
    )

    dialog.type_row.set_selected(1)  # bind (not bindd)
    dialog.key_entry.set_text("Q")
    dialog.modifiers_entry.set_text("$mainMod")
    dialog.description_entry.set_text("Test description")
    dialog.action_entry.set_text("exec")
    dialog.params_entry.set_text("alacritty")

    binding = dialog.get_binding()

    assert binding.type == BindType.BIND
    assert binding.key == "Q"
    assert binding.modifiers == ["$mainMod"]
    assert binding.description == "Test description"
    assert binding.action == "exec"
    assert binding.params == "alacritty"
    assert binding.submap is None
    assert binding.line_number >= 0


def test_get_binding_preserves_metadata(config_manager, mode_manager, sample_binding):
    """Test get_binding() preserves line_number and submap when editing."""
    dialog = BindingDialog(
        config_manager=config_manager,
        mode_manager=mode_manager,
        binding=sample_binding
    )

    # Change some fields
    dialog.key_entry.set_text("W")
    dialog.action_entry.set_text("exec")

    binding = dialog.get_binding()

    # Metadata should be preserved
    assert binding.line_number == 42
    assert binding.submap is None


def test_category_selector_shows_existing_categories(config_manager, mode_manager):
    """Test category selector shows existing categories plus Custom."""
    dialog = BindingDialog(
        config_manager=config_manager,
        mode_manager=mode_manager
    )

    model = dialog.category_row.get_model()
    categories = [model.get_string(i) for i in range(model.get_n_items())]

    assert "Applications" in categories
    assert "Window Management" in categories
    assert "Custom" in categories


def test_category_selector_defaults_to_custom(config_manager, mode_manager):
    """Test category selector defaults to Custom for new bindings."""
    dialog = BindingDialog(
        config_manager=config_manager,
        mode_manager=mode_manager
    )

    model = dialog.category_row.get_model()
    selected_category = model.get_string(dialog.category_row.get_selected())

    assert selected_category == "Custom"


def test_category_selector_set_for_existing_binding(config_manager, mode_manager, sample_binding):
    """Test category selector is set correctly for existing binding."""
    dialog = BindingDialog(
        config_manager=config_manager,
        mode_manager=mode_manager,
        binding=sample_binding
    )

    model = dialog.category_row.get_model()
    selected_category = model.get_string(dialog.category_row.get_selected())

    assert selected_category == "Window Management"


def test_bind_type_selector(config_manager, mode_manager):
    """Test bind type selector shows all types."""
    dialog = BindingDialog(
        config_manager=config_manager,
        mode_manager=mode_manager
    )

    model = dialog.type_row.get_model()
    types = [model.get_string(i) for i in range(model.get_n_items())]

    assert len(types) == 4
    assert "bindd (with description)" in types
    assert "bind (no description)" in types
    assert "bindel (on release)" in types
    assert "bindm (mouse)" in types


def test_successful_save_operation_new_binding(config_manager, mode_manager):
    """Test successful save operation for new binding."""
    # Mock add_binding to return success
    config_manager.add_binding = MagicMock(return_value=OperationResult(success=True))

    dialog = BindingDialog(
        config_manager=config_manager,
        mode_manager=mode_manager
    )
    dialog.key_entry.set_text("Q")
    dialog.action_entry.set_text("exec")

    # Mock close to verify it's called
    dialog.close = MagicMock()

    # Simulate save button click
    dialog._on_save_clicked(None)

    # Verify add_binding was called
    assert config_manager.add_binding.called
    assert config_manager.save.called
    # Verify dialog closed on success
    assert dialog.close.called


def test_successful_save_operation_edit_binding(config_manager, mode_manager, sample_binding):
    """Test successful save operation when editing."""
    # Mock mode_manager.apply_binding to return success (edit uses remove + add)
    mode_manager.apply_binding = MagicMock(return_value=OperationResult(success=True))

    dialog = BindingDialog(
        config_manager=config_manager,
        mode_manager=mode_manager,
        binding=sample_binding
    )
    dialog.key_entry.set_text("W")

    # Mock close to verify it's called
    dialog.close = MagicMock()

    # Simulate save button click
    dialog._on_save_clicked(None)

    # Verify mode_manager.apply_binding was called twice (remove old, add new)
    assert mode_manager.apply_binding.call_count == 2
    assert config_manager.save.called
    # Verify dialog closed on success
    assert dialog.close.called


def test_conflict_detection(config_manager, mode_manager):
    """Test conflict detection shows error with conflicting bindings."""
    conflicting_binding = Binding(
        type=BindType.BINDD,
        modifiers=["$mainMod"],
        key="Q",
        description="Conflicting binding",
        action="exec",
        params="",
        submap=None,
        line_number=10,
        category="Test",
    )

    # Mock add_binding to return conflict
    config_manager.add_binding = MagicMock(
        return_value=OperationResult(
            success=False,
            message="Binding conflicts with 1 existing binding(s)",
            conflicts=[conflicting_binding],
        )
    )

    dialog = BindingDialog(
        config_manager=config_manager,
        mode_manager=mode_manager
    )
    dialog.key_entry.set_text("Q")
    dialog.action_entry.set_text("exec")
    dialog.modifiers_entry.set_text("$mainMod")

    # Mock _show_error to verify it's called
    dialog._show_error = MagicMock()

    # Mock close to verify it's NOT called
    dialog.close = MagicMock()

    # Simulate save button click
    dialog._on_save_clicked(None)

    # Verify error was shown with conflict info
    assert dialog._show_error.called
    call_args = dialog._show_error.call_args[0]
    assert "Binding conflicts" in call_args[0]
    assert len(call_args[1]) == 1  # One conflict

    # Verify save was NOT called
    assert not config_manager.save.called

    # Verify dialog did NOT close (stays open for correction)
    assert not dialog.close.called


def test_validation_error_keeps_dialog_open(config_manager, mode_manager):
    """Test that validation errors keep dialog open for correction."""
    dialog = BindingDialog(
        config_manager=config_manager,
        mode_manager=mode_manager
    )

    # Set invalid input (empty key)
    dialog.key_entry.set_text("")
    dialog.action_entry.set_text("exec")

    # Mock _show_error to verify it's called
    dialog._show_error = MagicMock()

    # Mock close to verify it's NOT called
    dialog.close = MagicMock()

    # Mock add_binding to ensure it's not called
    config_manager.add_binding = MagicMock()

    # Simulate save button click
    dialog._on_save_clicked(None)

    # Verify error was shown
    assert dialog._show_error.called

    # Verify dialog did NOT close (stays open for correction)
    assert not dialog.close.called

    # Verify add_binding was NOT called (validation failed)
    assert not config_manager.add_binding.called


def test_cancel_button_closes_dialog(config_manager, mode_manager):
    """Test that cancel button closes dialog without saving."""
    dialog = BindingDialog(
        config_manager=config_manager,
        mode_manager=mode_manager
    )

    # Set some input
    dialog.key_entry.set_text("Q")
    dialog.action_entry.set_text("exec")

    # Mock close to verify it's called
    dialog.close = MagicMock()

    # Simulate cancel button click
    dialog._on_cancel_clicked(None)

    # Verify dialog closed
    assert dialog.close.called
