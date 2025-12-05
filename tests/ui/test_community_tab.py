"""Tests for community tab."""

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk
import pytest

from hyprbind.ui.community_tab import CommunityTab


def test_community_tab_has_profile_list():
    """Community tab has profile list widget."""
    tab = CommunityTab()

    assert tab.profile_list is not None
    assert isinstance(tab.profile_list, Gtk.ListView)


def test_community_tab_has_description_label():
    """Community tab has description label."""
    tab = CommunityTab()

    assert tab.description_label is not None
    assert isinstance(tab.description_label, Gtk.Label)


def test_community_tab_has_import_button():
    """Community tab has import button."""
    tab = CommunityTab()

    assert tab.import_button is not None
    assert isinstance(tab.import_button, Gtk.Button)


def test_import_button_disabled_initially():
    """Import button is disabled when no profile is selected."""
    tab = CommunityTab()

    assert not tab.import_button.get_sensitive()


def test_displays_popular_profiles():
    """Community tab displays list of popular profiles."""
    tab = CommunityTab()

    # Should have at least a few profiles
    assert len(tab.profiles) >= 3

    # Each profile should have required fields
    for profile in tab.profiles:
        assert "username" in profile
        assert "repo" in profile
        assert "description" in profile
        assert "stars" in profile


def test_selection_enables_import_button():
    """Selecting a profile enables the import button."""
    tab = CommunityTab()

    # Initially disabled
    assert not tab.import_button.get_sensitive()

    # Simulate selection by calling the handler directly
    # (GTK signals may not fire synchronously in unit tests)
    selection_model = tab.selection_model
    if selection_model and selection_model.get_n_items() > 0:
        # Set the selected item
        selection_model.set_selected(0)
        # Manually call the handler to test the logic
        tab._on_selection_changed(selection_model, 0, 1)
        # Selection handler should enable button
        assert tab.import_button.get_sensitive()
