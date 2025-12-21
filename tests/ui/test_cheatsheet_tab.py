"""Tests for cheatsheet tab."""

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk
import pytest
from pathlib import Path

from hyprbind.ui.cheatsheet_tab import CheatsheetTab
from hyprbind.core.config_manager import ConfigManager


@pytest.fixture
def sample_config_path():
    """Path to sample keybinds config."""
    return Path(__file__).parent.parent / "fixtures" / "sample_keybinds.conf"


@pytest.fixture
def manager(sample_config_path):
    """ConfigManager with loaded config."""
    mgr = ConfigManager(sample_config_path, skip_validation=True)
    mgr.load()
    return mgr


def test_cheatsheet_tab_has_grid_view(manager):
    """Cheatsheet tab has grid view for bindings."""
    tab = CheatsheetTab(manager)

    # Find GridView
    grid_view = None

    def find_grid_view(widget):
        nonlocal grid_view
        if isinstance(widget, Gtk.GridView):
            grid_view = widget
            return
        if hasattr(widget, "get_first_child"):
            child = widget.get_first_child()
            while child:
                find_grid_view(child)
                child = child.get_next_sibling()

    find_grid_view(tab)
    assert grid_view is not None


def test_cheatsheet_tab_has_export_buttons(manager):
    """Cheatsheet tab has export buttons."""
    tab = CheatsheetTab(manager)

    # Should have export buttons
    assert tab.export_pdf_btn is not None
    assert tab.export_html_btn is not None
    assert tab.export_md_btn is not None
