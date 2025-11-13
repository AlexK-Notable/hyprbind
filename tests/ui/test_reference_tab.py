"""Tests for reference tab."""

import gi
gi.require_version("Gtk", "4.0")

from gi.repository import Gtk
import pytest

from hyprbind.ui.reference_tab import ReferenceTab


def test_reference_tab_has_search_entry():
    """Reference tab contains search entry."""
    tab = ReferenceTab()

    # Find SearchEntry
    search_entry = None
    def find_search_entry(widget):
        nonlocal search_entry
        if isinstance(widget, Gtk.SearchEntry):
            search_entry = widget
            return
        if hasattr(widget, 'get_first_child'):
            child = widget.get_first_child()
            while child:
                find_search_entry(child)
                child = child.get_next_sibling()

    find_search_entry(tab)
    assert search_entry is not None, "Reference tab should have a SearchEntry"


def test_reference_tab_has_list_view():
    """Reference tab contains ListView for actions."""
    tab = ReferenceTab()

    # Find ListView
    list_view = None
    def find_list_view(widget):
        nonlocal list_view
        if isinstance(widget, Gtk.ListView):
            list_view = widget
            return
        if hasattr(widget, 'get_first_child'):
            child = widget.get_first_child()
            while child:
                find_list_view(child)
                child = child.get_next_sibling()

    find_list_view(tab)
    assert list_view is not None, "Reference tab should have a ListView"


def test_reference_tab_has_scrolled_window():
    """Reference tab contains ScrolledWindow."""
    tab = ReferenceTab()

    # Find ScrolledWindow
    scrolled = None
    def find_scrolled(widget):
        nonlocal scrolled
        if isinstance(widget, Gtk.ScrolledWindow):
            scrolled = widget
            return
        if hasattr(widget, 'get_first_child'):
            child = widget.get_first_child()
            while child:
                find_scrolled(child)
                child = child.get_next_sibling()

    find_scrolled(tab)
    assert scrolled is not None, "Reference tab should have a ScrolledWindow"


def test_reference_tab_displays_actions():
    """Reference tab displays action reference data."""
    tab = ReferenceTab()

    # Access list_view from the tab
    assert hasattr(tab, 'list_view'), "Tab should expose list_view attribute"

    model = tab.list_view.get_model()
    assert model is not None, "ListView should have a model"
    assert model.get_n_items() > 0, "Model should have items"


def test_reference_tab_has_filter_model():
    """Reference tab uses FilterListModel for search."""
    tab = ReferenceTab()

    assert hasattr(tab, 'filter_model'), "Tab should have filter_model"
    assert hasattr(tab, 'filter'), "Tab should have filter"
    assert hasattr(tab, 'list_store'), "Tab should have list_store"


def test_reference_tab_search_functionality():
    """Search entry filters displayed actions."""
    tab = ReferenceTab()

    # Get initial count
    initial_count = tab.filter_model.get_n_items()
    assert initial_count > 0

    # Set search text
    tab.search_entry.set_text("exec")

    # Filter should have changed
    filtered_count = tab.filter_model.get_n_items()

    # Should have fewer items (unless every action contains "exec")
    assert filtered_count <= initial_count
    assert filtered_count > 0, "Should find at least one action matching 'exec'"


def test_reference_tab_search_case_insensitive():
    """Search is case-insensitive."""
    tab = ReferenceTab()

    # Test with uppercase
    tab.search_entry.set_text("EXEC")
    count_upper = tab.filter_model.get_n_items()

    # Test with lowercase
    tab.search_entry.set_text("exec")
    count_lower = tab.filter_model.get_n_items()

    assert count_upper == count_lower, "Search should be case-insensitive"
    assert count_upper > 0, "Should find results"


def test_reference_tab_empty_search_shows_all():
    """Empty search shows all actions."""
    tab = ReferenceTab()

    # Set empty search
    tab.search_entry.set_text("")

    # Should show all items
    total_actions = tab.list_store.get_n_items()
    filtered_count = tab.filter_model.get_n_items()

    assert filtered_count == total_actions, "Empty search should show all actions"
