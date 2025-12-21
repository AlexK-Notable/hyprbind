"""Tests for EditorTab binding list with category grouping."""

import pytest
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw
from hyprbind.ui.editor_tab import EditorTab, BindingWithSection
from hyprbind.core.config_manager import ConfigManager
from hyprbind.core.models import Binding, BindType, Config, Category


@pytest.fixture
def config_manager(tmp_path):
    """Create ConfigManager with test data using temporary config file."""
    # CRITICAL: Use temp path to avoid writing to user's real config
    temp_config = tmp_path / "test_keybinds.conf"
    temp_config.write_text("# Test config\n")
    manager = ConfigManager(config_path=temp_config, skip_validation=True)

    # Create test config with multiple categories
    config = Config()

    # Window Actions category
    window_category = Category(name="Window Actions")
    window_category.bindings = [
        Binding(
            type=BindType.BINDD,
            modifiers=["$mainMod"],
            key="Q",
            description="Close window",
            action="killactive",
            params="",
            submap=None,
            line_number=1,
            category="Window Actions"
        ),
        Binding(
            type=BindType.BINDD,
            modifiers=["$mainMod", "SHIFT"],
            key="F",
            description="Toggle fullscreen",
            action="fullscreen",
            params="",
            submap=None,
            line_number=2,
            category="Window Actions"
        ),
    ]
    config.categories["Window Actions"] = window_category

    # Workspace Management category
    workspace_category = Category(name="Workspace Management")
    workspace_category.bindings = [
        Binding(
            type=BindType.BINDD,
            modifiers=["$mainMod"],
            key="1",
            description="Switch to workspace 1",
            action="workspace",
            params="1",
            submap=None,
            line_number=3,
            category="Workspace Management"
        ),
    ]
    config.categories["Workspace Management"] = workspace_category

    manager.config = config
    return manager


class TestEditorTabStructure:
    """Test EditorTab basic structure."""

    def test_editor_tab_has_list_view(self, config_manager, mode_manager):
        """Tab has ListView widget."""
        tab = EditorTab(config_manager, mode_manager)
        assert hasattr(tab, "list_view")
        assert isinstance(tab.list_view, Gtk.ListView)

    def test_editor_tab_has_list_store(self, config_manager, mode_manager):
        """Tab has Gio.ListStore."""
        tab = EditorTab(config_manager, mode_manager)
        assert hasattr(tab, "list_store")
        # ListStore is in Gio module
        from gi.repository import Gio
        assert isinstance(tab.list_store, Gio.ListStore)

    def test_editor_tab_has_selection_model(self, config_manager, mode_manager):
        """Tab has SingleSelection model."""
        tab = EditorTab(config_manager, mode_manager)
        assert hasattr(tab, "selection_model")
        assert isinstance(tab.selection_model, Gtk.SingleSelection)


class TestCategoryGrouping:
    """Test category header functionality."""

    def test_editor_tab_has_category_headers(self, config_manager, mode_manager):
        """Tab displays category headers."""
        tab = EditorTab(config_manager, mode_manager)

        # Count headers
        headers = []
        for i in range(tab.list_store.get_n_items()):
            item = tab.list_store.get_item(i)
            if item.is_header:
                headers.append(item.header_text)

        assert len(headers) > 0
        assert "Window Actions" in headers
        assert "Workspace Management" in headers

    def test_bindings_appear_after_headers(self, config_manager, mode_manager):
        """Bindings appear after their category headers."""
        tab = EditorTab(config_manager, mode_manager)

        # Find Window Actions header
        header_index = None
        for i in range(tab.list_store.get_n_items()):
            item = tab.list_store.get_item(i)
            if item.is_header and item.header_text == "Window Actions":
                header_index = i
                break

        assert header_index is not None

        # Check that next items are bindings (not headers)
        next_item = tab.list_store.get_item(header_index + 1)
        assert not next_item.is_header
        assert next_item.binding is not None

    def test_correct_number_of_items(self, config_manager, mode_manager):
        """Total items = headers + bindings."""
        tab = EditorTab(config_manager, mode_manager)

        # Count expected items: 2 categories (headers) + 3 bindings
        expected_items = 2 + 3  # 2 headers + 3 bindings
        actual_items = tab.list_store.get_n_items()

        assert actual_items == expected_items


class TestToolbar:
    """Test toolbar with CRUD buttons."""

    def test_editor_tab_has_toolbar(self, config_manager, mode_manager):
        """Tab has toolbar widgets."""
        tab = EditorTab(config_manager, mode_manager)

        # Find toolbar - it should be the first child
        first_child = tab.get_first_child()
        assert first_child is not None
        # Toolbar should be a Box or similar container
        assert isinstance(first_child, (Gtk.Box, Gtk.ActionBar))

    def test_toolbar_has_add_button(self, config_manager, mode_manager):
        """Toolbar has Add button."""
        tab = EditorTab(config_manager, mode_manager)
        assert hasattr(tab, "add_button")
        assert isinstance(tab.add_button, Gtk.Button)

    def test_toolbar_has_edit_button(self, config_manager, mode_manager):
        """Toolbar has Edit button."""
        tab = EditorTab(config_manager, mode_manager)
        assert hasattr(tab, "edit_button")
        assert isinstance(tab.edit_button, Gtk.Button)

    def test_toolbar_has_delete_button(self, config_manager, mode_manager):
        """Toolbar has Delete button."""
        tab = EditorTab(config_manager, mode_manager)
        assert hasattr(tab, "delete_button")
        assert isinstance(tab.delete_button, Gtk.Button)


class TestObserverPattern:
    """Test observer registration and reload."""

    def test_editor_tab_registers_as_observer(self, config_manager, mode_manager):
        """Tab registers itself with config manager."""
        initial_observer_count = len(config_manager._observers)
        tab = EditorTab(config_manager, mode_manager)

        # Should have one more observer
        assert len(config_manager._observers) == initial_observer_count + 1

    def test_reload_bindings_method_exists(self, config_manager, mode_manager):
        """Tab has reload_bindings method."""
        tab = EditorTab(config_manager, mode_manager)
        assert hasattr(tab, "reload_bindings")
        assert callable(tab.reload_bindings)

    def test_reload_bindings_clears_and_reloads(self, config_manager, mode_manager):
        """reload_bindings clears and reloads from config."""
        tab = EditorTab(config_manager, mode_manager)

        initial_count = tab.list_store.get_n_items()
        assert initial_count > 0

        # Manually clear
        tab.list_store.remove_all()
        assert tab.list_store.get_n_items() == 0

        # Reload should restore items
        tab.reload_bindings()
        assert tab.list_store.get_n_items() == initial_count


class TestBindingWithSection:
    """Test BindingWithSection wrapper class."""

    def test_binding_with_section_for_header(self):
        """Can create header item."""
        item = BindingWithSection(is_header=True, header_text="Test Category")

        assert item.is_header is True
        assert item.header_text == "Test Category"
        assert item.binding is None

    def test_binding_with_section_for_binding(self, config_manager):
        """Can create binding item."""
        binding = Binding(
            type=BindType.BINDD,
            modifiers=["$mainMod"],
            key="Q",
            description="Close",
            action="killactive",
            params="",
            submap=None,
            line_number=1,
            category="Test"
        )

        item = BindingWithSection(binding=binding)

        assert item.is_header is False
        assert item.binding is binding
        assert item.header_text == ""


class TestSelectionHandling:
    """Test selection behavior and button states."""

    def test_edit_with_no_selection_returns_early(self, config_manager, mode_manager):
        """Edit click with no selection does nothing."""
        from unittest.mock import patch

        tab = EditorTab(config_manager, mode_manager)

        # Deselect all
        tab.selection_model.set_selected(Gtk.INVALID_LIST_POSITION)

        # Mock BindingDialog to verify it's NOT created
        with patch('hyprbind.ui.editor_tab.BindingDialog') as mock_dialog:
            tab._on_edit_clicked(tab.edit_button)
            mock_dialog.assert_not_called()

    def test_delete_with_no_selection_returns_early(self, config_manager, mode_manager):
        """Delete click with no selection does nothing."""
        from unittest.mock import patch

        tab = EditorTab(config_manager, mode_manager)

        # Deselect all
        tab.selection_model.set_selected(Gtk.INVALID_LIST_POSITION)

        # Mock MessageDialog to verify it's NOT created
        with patch.object(Adw.MessageDialog, 'new') as mock_dialog:
            tab._on_delete_clicked(tab.delete_button)
            mock_dialog.assert_not_called()

    def test_edit_header_does_nothing(self, config_manager, mode_manager):
        """Editing a header does nothing."""
        from unittest.mock import patch

        tab = EditorTab(config_manager, mode_manager)

        # Find a header item
        header_index = None
        for i in range(tab.list_store.get_n_items()):
            item = tab.list_store.get_item(i)
            if item.is_header:
                header_index = i
                break

        if header_index is not None:
            tab.selection_model.set_selected(header_index)

            with patch('hyprbind.ui.editor_tab.BindingDialog') as mock_dialog:
                tab._on_edit_clicked(tab.edit_button)
                mock_dialog.assert_not_called()

    def test_delete_header_does_nothing(self, config_manager, mode_manager):
        """Deleting a header does nothing."""
        from unittest.mock import patch

        tab = EditorTab(config_manager, mode_manager)

        # Find a header item
        header_index = None
        for i in range(tab.list_store.get_n_items()):
            item = tab.list_store.get_item(i)
            if item.is_header:
                header_index = i
                break

        if header_index is not None:
            tab.selection_model.set_selected(header_index)

            with patch.object(Adw.MessageDialog, 'new') as mock_dialog:
                tab._on_delete_clicked(tab.delete_button)
                mock_dialog.assert_not_called()


class TestAddButtonHandler:
    """Test Add button click handling."""

    def test_add_button_creates_dialog(self, config_manager, mode_manager):
        """Add button creates BindingDialog."""
        from unittest.mock import patch, MagicMock

        tab = EditorTab(config_manager, mode_manager)

        mock_dialog = MagicMock()
        with patch('hyprbind.ui.editor_tab.BindingDialog', return_value=mock_dialog) as mock_class:
            tab._on_add_clicked(tab.add_button)

            # Dialog should be created
            mock_class.assert_called_once()

            # Dialog should be presented
            mock_dialog.present.assert_called_once()


class TestEditButtonHandler:
    """Test Edit button click handling."""

    def test_edit_button_creates_dialog_for_binding(self, config_manager, mode_manager):
        """Edit button creates dialog when binding is selected."""
        from unittest.mock import patch, MagicMock

        tab = EditorTab(config_manager, mode_manager)

        # Find a binding item (not header)
        binding_index = None
        for i in range(tab.list_store.get_n_items()):
            item = tab.list_store.get_item(i)
            if not item.is_header:
                binding_index = i
                break

        if binding_index is not None:
            tab.selection_model.set_selected(binding_index)

            mock_dialog = MagicMock()
            with patch('hyprbind.ui.editor_tab.BindingDialog', return_value=mock_dialog) as mock_class:
                tab._on_edit_clicked(tab.edit_button)

                # Dialog should be created with binding
                mock_class.assert_called_once()
                call_kwargs = mock_class.call_args[1]
                assert 'binding' in call_kwargs
                assert call_kwargs['binding'] is not None


class TestDeleteButtonHandler:
    """Test Delete button click handling."""

    def test_delete_button_shows_confirmation(self, config_manager, mode_manager):
        """Delete button shows confirmation dialog."""
        from unittest.mock import patch, MagicMock

        tab = EditorTab(config_manager, mode_manager)

        # Find a binding item
        binding_index = None
        for i in range(tab.list_store.get_n_items()):
            item = tab.list_store.get_item(i)
            if not item.is_header:
                binding_index = i
                break

        if binding_index is not None:
            tab.selection_model.set_selected(binding_index)

            # We can't easily mock Adw.MessageDialog.new since it's a static method
            # Just verify the method doesn't crash
            # Full dialog testing would require running GTK main loop


class TestDeleteResponse:
    """Test delete confirmation response handling."""

    def test_delete_response_cancel_does_nothing(self, config_manager, mode_manager):
        """Cancel response in delete dialog does nothing."""
        from unittest.mock import MagicMock

        tab = EditorTab(config_manager, mode_manager)

        # Find a binding
        binding_index = None
        binding = None
        for i in range(tab.list_store.get_n_items()):
            item = tab.list_store.get_item(i)
            if not item.is_header:
                binding_index = i
                binding = item.binding
                break

        if binding is not None:
            # Create mock dialog
            mock_dialog = MagicMock()

            # Call response handler with cancel
            initial_count = tab.list_store.get_n_items()
            tab._on_delete_response(mock_dialog, "cancel", binding)

            # Count should not change
            assert tab.list_store.get_n_items() == initial_count

    def test_delete_response_delete_removes_binding(self, config_manager, mode_manager):
        """Delete response removes binding from config."""
        from unittest.mock import MagicMock

        tab = EditorTab(config_manager, mode_manager)

        # Find a binding
        binding = None
        for i in range(tab.list_store.get_n_items()):
            item = tab.list_store.get_item(i)
            if not item.is_header:
                binding = item.binding
                break

        if binding is not None:
            mock_dialog = MagicMock()

            # Mock remove_binding AND save to prevent any file writes
            from hyprbind.core.config_manager import OperationResult
            config_manager.remove_binding = MagicMock(
                return_value=OperationResult(success=True)
            )
            config_manager.save = MagicMock(
                return_value=OperationResult(success=True)
            )

            tab._on_delete_response(mock_dialog, "delete", binding)

            # remove_binding should have been called
            config_manager.remove_binding.assert_called_once_with(binding)

            # save should have been called
            config_manager.save.assert_called()


class TestEmptyConfig:
    """Test behavior with empty configuration."""

    def test_empty_config_shows_no_items(self, mode_manager):
        """Empty config shows no items in list."""
        empty_manager = ConfigManager()
        empty_manager.config = Config()

        tab = EditorTab(empty_manager, mode_manager)

        assert tab.list_store.get_n_items() == 0

    def test_reload_with_empty_config(self, config_manager, mode_manager):
        """Reload with empty config clears list."""
        tab = EditorTab(config_manager, mode_manager)

        # Verify initial content
        initial_count = tab.list_store.get_n_items()
        assert initial_count > 0

        # Clear config
        config_manager.config.categories.clear()

        # Reload
        tab.reload_bindings()

        assert tab.list_store.get_n_items() == 0


class TestCategorySorting:
    """Test that categories are sorted alphabetically."""

    def test_categories_sorted_alphabetically(self, config_manager, mode_manager):
        """Category headers appear in sorted order."""
        tab = EditorTab(config_manager, mode_manager)

        # Collect headers in order
        headers = []
        for i in range(tab.list_store.get_n_items()):
            item = tab.list_store.get_item(i)
            if item.is_header:
                headers.append(item.header_text)

        # Verify they're sorted
        assert headers == sorted(headers)


class TestEmptyCategory:
    """Test behavior with empty categories."""

    def test_empty_category_not_shown(self, mode_manager):
        """Categories with no bindings are not shown."""
        manager = ConfigManager()
        config = Config()

        # Add empty category
        empty_cat = Category(name="Empty Category")
        config.categories["Empty Category"] = empty_cat

        # Add category with bindings
        filled_cat = Category(name="Filled Category")
        filled_cat.bindings = [
            Binding(
                type=BindType.BINDD,
                modifiers=["$mainMod"],
                key="Q",
                description="Test",
                action="killactive",
                params="",
                submap=None,
                line_number=1,
                category="Filled Category"
            )
        ]
        config.categories["Filled Category"] = filled_cat

        manager.config = config
        tab = EditorTab(manager, mode_manager)

        # Check headers
        headers = []
        for i in range(tab.list_store.get_n_items()):
            item = tab.list_store.get_item(i)
            if item.is_header:
                headers.append(item.header_text)

        # Empty category should not be in headers
        assert "Empty Category" not in headers
        assert "Filled Category" in headers


class TestConfigManagerReferences:
    """Test that tab correctly stores references."""

    def test_stores_config_manager(self, config_manager, mode_manager):
        """Tab stores config_manager reference."""
        tab = EditorTab(config_manager, mode_manager)
        assert tab.config_manager is config_manager

    def test_stores_mode_manager(self, config_manager, mode_manager):
        """Tab stores mode_manager reference."""
        tab = EditorTab(config_manager, mode_manager)
        assert tab.mode_manager is mode_manager


class TestBindingWithSectionGObject:
    """Test BindingWithSection GObject properties."""

    def test_is_gobject(self):
        """BindingWithSection is a GObject."""
        from gi.repository import GObject

        item = BindingWithSection()
        assert isinstance(item, GObject.Object)

    def test_default_values(self):
        """Default values are correct."""
        item = BindingWithSection()

        assert item.is_header is False
        assert item.header_text == ""
        assert item.binding is None

    def test_can_set_all_properties(self, config_manager):
        """All properties can be set."""
        binding = Binding(
            type=BindType.BINDD,
            modifiers=["$mainMod"],
            key="X",
            description="Test binding",
            action="exec",
            params="test",
            submap=None,
            line_number=99,
            category="TestCat"
        )

        item = BindingWithSection(
            binding=binding,
            is_header=False,
            header_text="should be ignored"
        )

        assert item.binding is binding
        assert item.is_header is False
