"""Tests for MainWindow tab structure and initialization."""

import pytest
import gi
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib
from hyprbind.ui.main_window import MainWindow
from hyprbind.core.config_manager import ConfigManager, OperationResult
from hyprbind.core.mode_manager import Mode


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


# =============================================================================
# Window Structure Tests
# =============================================================================


class TestWindowStructure:
    """Test window structure and initialization."""

    def test_window_is_adw_application_window(self, main_window):
        """Window is an Adw.ApplicationWindow."""
        assert isinstance(main_window, Adw.ApplicationWindow)

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

    def test_has_header_bar(self, main_window):
        """Window has header bar."""
        assert hasattr(main_window, "header_bar")
        assert isinstance(main_window.header_bar, Adw.HeaderBar)

    def test_has_main_content(self, main_window):
        """Window has main content box."""
        assert hasattr(main_window, "main_content")
        assert isinstance(main_window.main_content, Gtk.Box)


# =============================================================================
# Tab Structure Tests
# =============================================================================


class TestTabStructure:
    """Test tab titles and structure."""

    def test_editor_tab_first(self, main_window):
        """Editor tab is first."""
        page = main_window.tab_view.get_nth_page(0)
        assert page.get_title() == "Editor"

    def test_community_tab_second(self, main_window):
        """Community tab is second."""
        page = main_window.tab_view.get_nth_page(1)
        assert page.get_title() == "Community"

    def test_cheatsheet_tab_third(self, main_window):
        """Cheatsheet tab is third."""
        page = main_window.tab_view.get_nth_page(2)
        assert page.get_title() == "Cheatsheet"

    def test_reference_tab_fourth(self, main_window):
        """Reference tab is fourth."""
        page = main_window.tab_view.get_nth_page(3)
        assert page.get_title() == "Reference"


# =============================================================================
# Mode Manager Tests
# =============================================================================


class TestModeManager:
    """Test mode manager integration."""

    def test_mode_manager_initialized(self, main_window):
        """Mode manager is initialized."""
        assert hasattr(main_window, "mode_manager")
        from hyprbind.core.mode_manager import ModeManager
        assert isinstance(main_window.mode_manager, ModeManager)

    def test_mode_manager_has_config_manager(self, main_window):
        """Mode manager references the same config manager."""
        assert main_window.mode_manager.config_manager is main_window.config_manager


# =============================================================================
# Mode Toggle Tests
# =============================================================================


class TestModeToggle:
    """Test mode toggle switch functionality."""

    def test_has_mode_switch(self, main_window):
        """Window has mode switch."""
        assert hasattr(main_window, "mode_switch")
        assert isinstance(main_window.mode_switch, Gtk.Switch)

    def test_has_mode_label(self, main_window):
        """Window has mode label."""
        assert hasattr(main_window, "mode_label")
        assert isinstance(main_window.mode_label, Gtk.Label)

    def test_mode_switch_off_by_default(self, main_window):
        """Mode switch is off (Safe mode) by default."""
        assert not main_window.mode_switch.get_active()

    def test_mode_label_shows_safe_by_default(self, main_window):
        """Mode label shows 'Safe' by default."""
        assert main_window.mode_label.get_text() == "Safe"

    def test_has_mode_toggle_handler(self, main_window):
        """Window has mode toggle handler."""
        assert hasattr(main_window, "_on_mode_toggled")
        assert callable(main_window._on_mode_toggled)

    def test_has_update_mode_ui_method(self, main_window):
        """Window has mode UI update method."""
        assert hasattr(main_window, "_update_mode_ui")
        assert callable(main_window._update_mode_ui)

    def test_update_mode_ui_safe(self, main_window):
        """Update mode UI shows Safe state correctly."""
        with patch.object(main_window.mode_manager, "get_mode", return_value=Mode.SAFE):
            main_window._update_mode_ui()
            assert main_window.mode_label.get_text() == "Safe"
            assert not main_window.live_mode_banner.get_revealed()

    def test_update_mode_ui_live(self, main_window):
        """Update mode UI shows Live state correctly."""
        with patch.object(main_window.mode_manager, "get_mode", return_value=Mode.LIVE):
            main_window._update_mode_ui()
            assert main_window.mode_label.get_text() == "Live"
            assert main_window.live_mode_banner.get_revealed()


# =============================================================================
# Live Mode Banner Tests
# =============================================================================


class TestLiveModeBanner:
    """Test live mode banner functionality."""

    def test_has_live_mode_banner(self, main_window):
        """Window has live mode banner."""
        assert hasattr(main_window, "live_mode_banner")
        assert isinstance(main_window.live_mode_banner, Adw.Banner)

    def test_live_mode_banner_hidden_by_default(self, main_window):
        """Live mode banner is hidden by default."""
        assert not main_window.live_mode_banner.get_revealed()

    def test_has_live_save_handler(self, main_window):
        """Window has live save handler."""
        assert hasattr(main_window, "_on_live_save_clicked")
        assert callable(main_window._on_live_save_clicked)


# =============================================================================
# Live Mode Confirmation Tests
# =============================================================================


class TestLiveModeConfirmation:
    """Test live mode confirmation dialog."""

    def test_has_confirmation_method(self, main_window):
        """Window has live mode confirmation method."""
        assert hasattr(main_window, "_show_live_mode_confirmation")
        assert callable(main_window._show_live_mode_confirmation)

    def test_mode_toggle_checks_availability(self, main_window):
        """Mode toggle checks if live mode is available."""
        with patch.object(main_window.mode_manager, "is_live_available", return_value=False):
            with patch.object(main_window, "_show_error_dialog") as mock_error:
                # Simulate switch activation
                main_window.mode_switch.set_active(True)
                main_window._on_mode_toggled(main_window.mode_switch, None)

                # Should show error and revert switch
                mock_error.assert_called_once()
                assert "Live Mode Unavailable" in mock_error.call_args[0][0]


# =============================================================================
# Async Loading Tests
# =============================================================================


class TestAsyncLoading:
    """Test asynchronous config loading behavior."""

    def test_has_loading_methods(self, main_window):
        """Window has loading indicator methods."""
        assert hasattr(main_window, "_show_loading")
        assert hasattr(main_window, "_hide_loading")

    def test_has_async_load_method(self, main_window):
        """Window has async loading method."""
        assert hasattr(main_window, "_load_config_async")

    def test_has_loading_box(self, main_window):
        """Window has loading box widget."""
        assert hasattr(main_window, "loading_box")
        assert isinstance(main_window.loading_box, Gtk.Box)

    def test_has_loading_spinner(self, main_window):
        """Window has loading spinner widget."""
        assert hasattr(main_window, "loading_spinner")
        assert isinstance(main_window.loading_spinner, Gtk.Spinner)

    def test_show_loading_shows_box(self, main_window):
        """Show loading makes loading box visible."""
        main_window._show_loading()
        assert main_window.loading_box.get_visible()

    def test_hide_loading_hides_box(self, main_window):
        """Hide loading makes loading box invisible."""
        main_window._show_loading()
        main_window._hide_loading()
        assert not main_window.loading_box.get_visible()

    def test_has_config_loaded_callback(self, main_window):
        """Window has config loaded callback."""
        assert hasattr(main_window, "_on_config_loaded")
        assert callable(main_window._on_config_loaded)

    def test_has_config_load_error_callback(self, main_window):
        """Window has config load error callback."""
        assert hasattr(main_window, "_on_config_load_error")
        assert callable(main_window._on_config_load_error)

    def test_config_loaded_hides_loading(self, main_window):
        """Config loaded callback hides loading."""
        main_window._show_loading()
        main_window._on_config_loaded()
        assert not main_window.loading_box.get_visible()


# =============================================================================
# Observer Integration Tests
# =============================================================================


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

    def test_has_config_changed_callback(self, main_window):
        """Window has config changed callback."""
        assert hasattr(main_window, "_on_config_changed")
        assert callable(main_window._on_config_changed)


# =============================================================================
# Chezmoi Integration Tests
# =============================================================================


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


# =============================================================================
# Theming Tests
# =============================================================================


class TestTheming:
    """Test theming integration."""

    def test_has_setup_theming_method(self, main_window):
        """Window has theming setup method."""
        assert hasattr(main_window, "_setup_theming")
        assert callable(main_window._setup_theming)

    def test_has_theme_manager(self, main_window):
        """Window has theme manager."""
        assert hasattr(main_window, "theme_manager")


# =============================================================================
# Close Request Tests
# =============================================================================


class TestCloseRequest:
    """Test window close request handling."""

    def test_has_close_request_handler(self, main_window):
        """Window has close request handler."""
        assert hasattr(main_window, "do_close_request")
        assert callable(main_window.do_close_request)

    def test_has_close_dialog_response_handler(self, main_window):
        """Window has close dialog response handler."""
        assert hasattr(main_window, "_on_close_dialog_response")
        assert callable(main_window._on_close_dialog_response)

    def test_close_allowed_when_not_dirty(self, main_window):
        """Close is allowed when no unsaved changes."""
        with patch.object(main_window.config_manager, "is_dirty", return_value=False):
            result = main_window.do_close_request()
            assert result is False  # False means allow close

    def test_close_prevented_when_dirty(self, main_window):
        """Close is prevented when there are unsaved changes."""
        with patch.object(main_window.config_manager, "is_dirty", return_value=True):
            # Note: do_close_request will try to show a dialog
            # We need to handle that gracefully
            result = main_window.do_close_request()
            assert result is True  # True means prevent close

    def test_discard_response_destroys_window(self, main_window):
        """Discard response destroys window."""
        mock_dialog = MagicMock()

        with patch.object(main_window, "destroy") as mock_destroy:
            main_window._on_close_dialog_response(mock_dialog, "discard")
            mock_destroy.assert_called_once()

    def test_cancel_response_keeps_window_open(self, main_window):
        """Cancel response keeps window open."""
        mock_dialog = MagicMock()

        with patch.object(main_window, "destroy") as mock_destroy:
            main_window._on_close_dialog_response(mock_dialog, "cancel")
            mock_destroy.assert_not_called()

    def test_save_response_saves_and_destroys_on_success(self, main_window):
        """Save response saves and destroys on success."""
        mock_dialog = MagicMock()

        with patch.object(
            main_window.config_manager, "save",
            return_value=OperationResult(success=True)
        ):
            with patch.object(main_window, "destroy") as mock_destroy:
                main_window._on_close_dialog_response(mock_dialog, "save")
                mock_destroy.assert_called_once()

    def test_save_response_shows_error_on_failure(self, main_window):
        """Save response shows error dialog on failure."""
        mock_dialog = MagicMock()

        with patch.object(
            main_window.config_manager, "save",
            return_value=OperationResult(success=False, message="Test error")
        ):
            with patch.object(main_window, "destroy") as mock_destroy:
                main_window._on_close_dialog_response(mock_dialog, "save")
                # Window should NOT be destroyed on save failure
                mock_destroy.assert_not_called()


# =============================================================================
# Error Dialog Tests
# =============================================================================


class TestErrorDialog:
    """Test error dialog functionality."""

    def test_has_error_dialog_method(self, main_window):
        """Window has error dialog method."""
        assert hasattr(main_window, "_show_error_dialog")
        assert callable(main_window._show_error_dialog)


# =============================================================================
# Live Mode Save Tests
# =============================================================================


class TestLiveModeSave:
    """Test live mode save functionality."""

    def test_live_save_calls_config_save(self, main_window):
        """Live save button calls config manager save."""
        with patch.object(
            main_window.config_manager, "save",
            return_value=OperationResult(success=True)
        ) as mock_save:
            main_window._on_live_save_clicked(main_window.live_mode_banner)
            mock_save.assert_called_once()

    def test_live_save_shows_error_on_failure(self, main_window):
        """Live save shows error dialog on failure."""
        with patch.object(
            main_window.config_manager, "save",
            return_value=OperationResult(success=False, message="Test error")
        ):
            with patch.object(main_window, "_show_error_dialog") as mock_error:
                main_window._on_live_save_clicked(main_window.live_mode_banner)
                mock_error.assert_called_once()
                assert "Save Failed" in mock_error.call_args[0][0]


# =============================================================================
# Tab Reference Tests
# =============================================================================


class TestTabReferences:
    """Test that tab references are properly stored."""

    def test_editor_tab_is_correct_type(self, main_window):
        """Editor tab is EditorTab instance."""
        from hyprbind.ui.editor_tab import EditorTab
        assert isinstance(main_window.editor_tab, EditorTab)

    def test_community_tab_is_correct_type(self, main_window):
        """Community tab is CommunityTab instance."""
        from hyprbind.ui.community_tab import CommunityTab
        assert isinstance(main_window.community_tab, CommunityTab)

    def test_cheatsheet_tab_is_correct_type(self, main_window):
        """Cheatsheet tab is CheatsheetTab instance."""
        from hyprbind.ui.cheatsheet_tab import CheatsheetTab
        assert isinstance(main_window.cheatsheet_tab, CheatsheetTab)

    def test_reference_tab_is_correct_type(self, main_window):
        """Reference tab is ReferenceTab instance."""
        from hyprbind.ui.reference_tab import ReferenceTab
        assert isinstance(main_window.reference_tab, ReferenceTab)


# =============================================================================
# Setup Methods Tests
# =============================================================================


class TestSetupMethods:
    """Test setup method existence."""

    def test_has_setup_tabs_method(self, main_window):
        """Window has setup tabs method."""
        assert hasattr(main_window, "_setup_tabs")
        assert callable(main_window._setup_tabs)

    def test_has_setup_mode_toggle_method(self, main_window):
        """Window has setup mode toggle method."""
        assert hasattr(main_window, "_setup_mode_toggle")
        assert callable(main_window._setup_mode_toggle)


# =============================================================================
# UI File Path Tests
# =============================================================================


class TestUIFilePath:
    """Test UI file path resolution."""

    def test_get_ui_file_path_function_exists(self):
        """UI file path function exists."""
        from hyprbind.ui.main_window import _get_ui_file_path
        assert callable(_get_ui_file_path)

    def test_ui_file_path_returns_path(self):
        """UI file path function returns a Path object."""
        from hyprbind.ui.main_window import _get_ui_file_path
        path = _get_ui_file_path()
        assert isinstance(path, Path)

    def test_ui_file_exists(self):
        """UI file actually exists."""
        from hyprbind.ui.main_window import _UI_FILE
        assert _UI_FILE.exists()
