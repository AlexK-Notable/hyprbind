"""Tests for MainWindow tab structure and initialization."""

import pytest
import gi
from pathlib import Path
from unittest.mock import Mock, patch

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
        assert hasattr(main_window, "community_tab")
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


class TestChezmoiIntegration:
    """Test Chezmoi integration features."""

    def test_window_has_chezmoi_banner(self, main_window):
        """Window has Chezmoi banner widget."""
        assert hasattr(main_window, "chezmoi_banner")
        assert isinstance(main_window.chezmoi_banner, Adw.Banner)

    def test_chezmoi_banner_hidden_by_default(self, main_window):
        """Chezmoi banner is hidden by default."""
        assert not main_window.chezmoi_banner.get_revealed()

    def test_has_chezmoi_setup_method(self, main_window):
        """Window has Chezmoi setup method."""
        assert hasattr(main_window, "_setup_chezmoi_banner")

    def test_has_chezmoi_check_method(self, main_window):
        """Window has Chezmoi check method."""
        assert hasattr(main_window, "_check_chezmoi_management")

    def test_has_chezmoi_learn_more_handler(self, main_window):
        """Window has Chezmoi learn more handler."""
        assert hasattr(main_window, "_on_chezmoi_learn_more")

    @patch("hyprbind.integrations.chezmoi.ChezmoiIntegration.is_managed")
    @patch("hyprbind.integrations.chezmoi.ChezmoiIntegration.get_source_path")
    def test_banner_shows_when_file_is_managed(
        self, mock_get_source, mock_is_managed, main_window
    ):
        """Banner shows when config file is managed by Chezmoi."""
        # Setup mocks
        mock_is_managed.return_value = True
        mock_get_source.return_value = Path(
            "/home/user/.local/share/chezmoi/dot_config/hypr/config/keybinds.conf"
        )
        main_window.config_manager.config_path = Path(
            "/home/user/.config/hypr/config/keybinds.conf"
        )

        # Call check method
        main_window._check_chezmoi_management()

        # Banner should be revealed
        assert main_window.chezmoi_banner.get_revealed()

    @patch("hyprbind.integrations.chezmoi.ChezmoiIntegration.is_managed")
    def test_banner_stays_hidden_when_file_not_managed(self, mock_is_managed, main_window):
        """Banner stays hidden when config file is not managed by Chezmoi."""
        # Setup mocks
        mock_is_managed.return_value = False
        main_window.config_manager.config_path = Path(
            "/home/user/.config/hypr/config/keybinds.conf"
        )

        # Call check method
        main_window._check_chezmoi_management()

        # Banner should still be hidden
        assert not main_window.chezmoi_banner.get_revealed()

    @patch("hyprbind.integrations.chezmoi.ChezmoiIntegration.is_managed")
    @patch("hyprbind.integrations.chezmoi.ChezmoiIntegration.get_source_path")
    def test_banner_title_includes_source_filename(
        self, mock_get_source, mock_is_managed, main_window
    ):
        """Banner title includes the source filename."""
        # Setup mocks
        source_path = Path("/home/user/.local/share/chezmoi/dot_config/hypr/config/keybinds.conf")
        mock_is_managed.return_value = True
        mock_get_source.return_value = source_path
        main_window.config_manager.config_path = Path(
            "/home/user/.config/hypr/config/keybinds.conf"
        )

        # Call check method
        main_window._check_chezmoi_management()

        # Banner title should include source filename
        title = main_window.chezmoi_banner.get_title()
        assert source_path.name in title
