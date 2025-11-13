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
def config_manager():
    """Create ConfigManager with test data."""
    manager = ConfigManager()

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

    def test_editor_tab_has_list_view(self, config_manager):
        """Tab has ListView widget."""
        tab = EditorTab(config_manager)
        assert hasattr(tab, "list_view")
        assert isinstance(tab.list_view, Gtk.ListView)

    def test_editor_tab_has_list_store(self, config_manager):
        """Tab has Gio.ListStore."""
        tab = EditorTab(config_manager)
        assert hasattr(tab, "list_store")
        # ListStore is in Gio module
        from gi.repository import Gio
        assert isinstance(tab.list_store, Gio.ListStore)

    def test_editor_tab_has_selection_model(self, config_manager):
        """Tab has SingleSelection model."""
        tab = EditorTab(config_manager)
        assert hasattr(tab, "selection_model")
        assert isinstance(tab.selection_model, Gtk.SingleSelection)


class TestCategoryGrouping:
    """Test category header functionality."""

    def test_editor_tab_has_category_headers(self, config_manager):
        """Tab displays category headers."""
        tab = EditorTab(config_manager)

        # Count headers
        headers = []
        for i in range(tab.list_store.get_n_items()):
            item = tab.list_store.get_item(i)
            if item.is_header:
                headers.append(item.header_text)

        assert len(headers) > 0
        assert "Window Actions" in headers
        assert "Workspace Management" in headers

    def test_bindings_appear_after_headers(self, config_manager):
        """Bindings appear after their category headers."""
        tab = EditorTab(config_manager)

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

    def test_correct_number_of_items(self, config_manager):
        """Total items = headers + bindings."""
        tab = EditorTab(config_manager)

        # Count expected items: 2 categories (headers) + 3 bindings
        expected_items = 2 + 3  # 2 headers + 3 bindings
        actual_items = tab.list_store.get_n_items()

        assert actual_items == expected_items


class TestToolbar:
    """Test toolbar with CRUD buttons."""

    def test_editor_tab_has_toolbar(self, config_manager):
        """Tab has toolbar widgets."""
        tab = EditorTab(config_manager)

        # Find toolbar - it should be the first child
        first_child = tab.get_first_child()
        assert first_child is not None
        # Toolbar should be a Box or similar container
        assert isinstance(first_child, (Gtk.Box, Gtk.ActionBar))

    def test_toolbar_has_add_button(self, config_manager):
        """Toolbar has Add button."""
        tab = EditorTab(config_manager)
        assert hasattr(tab, "add_button")
        assert isinstance(tab.add_button, Gtk.Button)

    def test_toolbar_has_edit_button(self, config_manager):
        """Toolbar has Edit button."""
        tab = EditorTab(config_manager)
        assert hasattr(tab, "edit_button")
        assert isinstance(tab.edit_button, Gtk.Button)

    def test_toolbar_has_delete_button(self, config_manager):
        """Toolbar has Delete button."""
        tab = EditorTab(config_manager)
        assert hasattr(tab, "delete_button")
        assert isinstance(tab.delete_button, Gtk.Button)


class TestObserverPattern:
    """Test observer registration and reload."""

    def test_editor_tab_registers_as_observer(self, config_manager):
        """Tab registers itself with config manager."""
        initial_observer_count = len(config_manager._observers)
        tab = EditorTab(config_manager)

        # Should have one more observer
        assert len(config_manager._observers) == initial_observer_count + 1

    def test_reload_bindings_method_exists(self, config_manager):
        """Tab has reload_bindings method."""
        tab = EditorTab(config_manager)
        assert hasattr(tab, "reload_bindings")
        assert callable(tab.reload_bindings)

    def test_reload_bindings_clears_and_reloads(self, config_manager):
        """reload_bindings clears and reloads from config."""
        tab = EditorTab(config_manager)

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
