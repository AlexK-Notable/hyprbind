"""Tests for MainWindow tab structure and initialization."""

import pytest
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib
from hyprbind.ui.main_window import MainWindow
from hyprbind.core.config_manager import ConfigManager


@pytest.fixture
def app():
    """Create GTK application."""
    application = Adw.Application(application_id="dev.hyprbind.test")
    return application


@pytest.fixture
def main_window(app):
    """Create MainWindow instance."""
    window = MainWindow(application=app)
    return window


class TestWindowStructure:
    """Test window structure and initialization."""

    def test_window_has_tab_view(self, main_window):
        """Window has tab view."""
        assert hasattr(main_window, "tab_view")
        assert isinstance(main_window.tab_view, Adw.TabView)

    def test_window_has_four_tabs(self, main_window):
        """Window has four tabs."""
        assert main_window.tab_view.get_n_pages() == 4

    def test_config_manager_initialized(self, main_window):
        """Config manager is initialized."""
        assert hasattr(main_window, "config_manager")
        assert isinstance(main_window.config_manager, ConfigManager)

    def test_tabs_stored_as_attributes(self, main_window):
        """Tabs are accessible as direct attributes."""
        assert hasattr(main_window, "editor_tab")
        assert hasattr(main_window, "conflicts_tab")
        assert hasattr(main_window, "cheatsheet_tab")
        assert hasattr(main_window, "reference_tab")


class TestAsyncLoading:
    """Test asynchronous config loading behavior."""

    def test_has_loading_methods(self, main_window):
        """Window has loading indicator methods."""
        assert hasattr(main_window, "_show_loading")
        assert hasattr(main_window, "_hide_loading")

    def test_has_async_load_method(self, main_window):
        """Window has async loading method."""
        assert hasattr(main_window, "_load_config_async")


class TestObserverIntegration:
    """Test observer pattern integration."""

    def test_window_registers_as_observer(self, main_window):
        """Window registers itself as config observer."""
        # Check that window has observer callback method
        assert hasattr(main_window, "_on_config_changed")

        # ConfigManager should have at least one observer registered
        # (The window should register itself during initialization)
        # Note: This test may need adjustment based on when observer registration happens
        assert len(main_window.config_manager._observers) > 0
