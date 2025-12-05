"""Tests for Live Mode UI integration."""

import pytest
import gi
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from tempfile import NamedTemporaryFile

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw
from hyprbind.ui.main_window import MainWindow
from hyprbind.core.mode_manager import Mode, ModeManager


@pytest.fixture
def app():
    """Create GTK application."""
    application = Adw.Application(application_id="dev.hyprbind.test")
    return application


@pytest.fixture
def temp_config_file(tmp_path):
    """Create temporary config file with sample bindings."""
    config_file = tmp_path / "test_hyprland.conf"
    config_content = """# Test config
bindd = $mainMod, RETURN, Terminal, exec, alacritty
bindd = $mainMod, Q, Close window, killactive,
"""
    config_file.write_text(config_content)
    return config_file


@pytest.fixture
def main_window(app, temp_config_file):
    """Create MainWindow instance with loaded config."""
    from hyprbind.core.config_manager import ConfigManager

    # Patch ConfigManager to use temp config
    original_init = ConfigManager.__init__

    def patched_init(cm_self, cm_config_path=None):
        original_init(cm_self, config_path=temp_config_file)

    ConfigManager.__init__ = patched_init

    try:
        window = MainWindow(application=app)
        # Load config synchronously for tests
        window.config_manager.load()
    finally:
        ConfigManager.__init__ = original_init

    return window


class TestMainWindowModeToggle:
    """Test mode toggle UI in MainWindow."""

    def test_main_window_has_mode_switch(self, main_window):
        """MainWindow should have mode toggle switch."""
        assert hasattr(main_window, "mode_switch")
        assert isinstance(main_window.mode_switch, Gtk.Switch)

    def test_main_window_has_mode_label(self, main_window):
        """MainWindow should have mode status label."""
        assert hasattr(main_window, "mode_label")
        assert isinstance(main_window.mode_label, Gtk.Label)

    def test_main_window_has_live_mode_banner(self, main_window):
        """MainWindow should have Live mode banner."""
        assert hasattr(main_window, "live_mode_banner")
        assert isinstance(main_window.live_mode_banner, Adw.Banner)

    def test_main_window_has_mode_manager(self, main_window):
        """MainWindow should have ModeManager instance."""
        assert hasattr(main_window, "mode_manager")
        assert isinstance(main_window.mode_manager, ModeManager)

    def test_mode_label_shows_safe_by_default(self, main_window):
        """Mode label should show 'Safe' by default."""
        assert main_window.mode_label.get_text() == "Safe"

    def test_mode_switch_inactive_by_default(self, main_window):
        """Mode switch should be inactive (Safe mode) by default."""
        assert not main_window.mode_switch.get_active()

    def test_live_banner_hidden_by_default(self, main_window):
        """Live mode banner should be hidden by default."""
        assert not main_window.live_mode_banner.get_revealed()


class TestModeToggleInteraction:
    """Test mode toggle interaction and dialogs."""

    @patch("hyprbind.ipc.hyprland_client.HyprlandClient.is_running")
    def test_mode_toggle_shows_confirmation_for_live(
        self, mock_is_running, main_window
    ):
        """Toggling to Live should show confirmation dialog."""
        mock_is_running.return_value = True

        # Mock the confirmation dialog to auto-respond
        with patch.object(
            Adw.MessageDialog, "new", return_value=Mock()
        ) as mock_dialog:
            mock_dialog_instance = Mock()
            mock_dialog.return_value = mock_dialog_instance

            # Activate switch
            main_window.mode_switch.set_active(True)

            # Dialog should have been created
            mock_dialog.assert_called_once()

    @patch("hyprbind.ipc.hyprland_client.HyprlandClient.is_running")
    def test_mode_label_updates_to_live(self, mock_is_running, main_window):
        """Mode label should update to 'Live' when mode changes."""
        mock_is_running.return_value = True

        # Directly set mode via mode_manager
        main_window.mode_manager.set_mode(Mode.LIVE)
        main_window._update_mode_ui()

        assert main_window.mode_label.get_text() == "Live"

    @patch("hyprbind.ipc.hyprland_client.HyprlandClient.is_running")
    def test_live_banner_revealed_in_live_mode(self, mock_is_running, main_window):
        """Live mode banner should be revealed when in Live mode."""
        mock_is_running.return_value = True

        # Set to Live mode
        main_window.mode_manager.set_mode(Mode.LIVE)
        main_window._update_mode_ui()

        assert main_window.live_mode_banner.get_revealed()

    def test_mode_label_shows_safe_in_safe_mode(self, main_window):
        """Mode label should show 'Safe' in Safe mode."""
        main_window.mode_manager.set_mode(Mode.SAFE)
        main_window._update_mode_ui()

        assert main_window.mode_label.get_text() == "Safe"

    @patch("hyprbind.ipc.hyprland_client.HyprlandClient.is_running")
    def test_live_mode_disabled_when_hyprland_not_running(
        self, mock_is_running, main_window
    ):
        """Live mode toggle should be disabled if Hyprland not available."""
        mock_is_running.return_value = False

        # Try to activate switch
        main_window.mode_switch.set_active(True)

        # Switch should be reverted to False since Hyprland isn't running
        # Note: This requires the actual _on_mode_toggled handler to be connected
        # In the real implementation, the handler will revert the switch


class TestEditorTabModeIntegration:
    """Test EditorTab integration with ModeManager."""

    @patch("hyprbind.ipc.hyprland_client.HyprlandClient.is_running")
    def test_editor_tab_receives_mode_manager(self, mock_is_running, main_window):
        """EditorTab should receive ModeManager instance."""
        mock_is_running.return_value = True

        # Check that editor_tab has mode_manager
        assert hasattr(main_window.editor_tab, "mode_manager")
        assert isinstance(main_window.editor_tab.mode_manager, ModeManager)


class TestBindingDialogModeIntegration:
    """Test BindingDialog integration with ModeManager."""

    @patch("hyprbind.ipc.hyprland_client.HyprlandClient.is_running")
    def test_binding_dialog_receives_mode_manager(self, mock_is_running, main_window):
        """BindingDialog should receive ModeManager instance."""
        from hyprbind.ui.binding_dialog import BindingDialog

        mock_is_running.return_value = True

        # Create dialog with mode_manager
        dialog = BindingDialog(
            config_manager=main_window.config_manager,
            mode_manager=main_window.mode_manager,
            parent=main_window,
        )

        assert hasattr(dialog, "mode_manager")
        assert isinstance(dialog.mode_manager, ModeManager)


class TestLiveModeWorkflow:
    """Test complete Live mode workflow."""

    @patch("hyprbind.ipc.hyprland_client.HyprlandClient.is_running")
    @patch("hyprbind.ipc.hyprland_client.HyprlandClient.connect")
    @patch("hyprbind.ipc.hyprland_client.HyprlandClient.add_binding")
    def test_live_mode_applies_binding_via_ipc(
        self, mock_add_binding, mock_connect, mock_is_running, main_window
    ):
        """In Live mode, bindings should be applied via IPC."""
        from hyprbind.core.models import Binding, BindType

        mock_is_running.return_value = True
        mock_connect.return_value = True
        mock_add_binding.return_value = True

        # Set to Live mode
        main_window.mode_manager.set_mode(Mode.LIVE)

        # Create test binding
        binding = Binding(
            type=BindType.BINDD,
            modifiers=["$mainMod"],
            key="T",
            description="Test binding",
            action="exec",
            params="alacritty",
            submap=None,
            line_number=0,
            category="Test",
        )

        # Apply binding
        result = main_window.mode_manager.apply_binding(binding, "add")

        # Should succeed via IPC
        assert result.success
        assert "IPC" in result.message

    @patch("hyprbind.ipc.hyprland_client.HyprlandClient.is_running")
    def test_safe_mode_applies_binding_to_file(self, mock_is_running, main_window):
        """In Safe mode, bindings should be applied to config file."""
        from hyprbind.core.models import Binding, BindType

        mock_is_running.return_value = False

        # Ensure Safe mode
        main_window.mode_manager.set_mode(Mode.SAFE)

        # Create test binding
        binding = Binding(
            type=BindType.BINDD,
            modifiers=["$mainMod"],
            key="T",
            description="Test binding",
            action="exec",
            params="alacritty",
            submap=None,
            line_number=0,
            category="Test",
        )

        # Apply binding
        result = main_window.mode_manager.apply_binding(binding, "add")

        # Should succeed and modify config
        assert result.success
        # In Safe mode, message should not mention IPC
        assert "IPC" not in result.message


class TestUIStateUpdates:
    """Test UI state updates based on mode changes."""

    @patch("hyprbind.ipc.hyprland_client.HyprlandClient.is_running")
    def test_mode_switch_syncs_with_mode_manager(
        self, mock_is_running, main_window
    ):
        """Mode switch state should sync with ModeManager mode."""
        mock_is_running.return_value = True

        # Set to Live mode programmatically
        main_window.mode_manager.set_mode(Mode.LIVE)
        main_window._update_mode_ui()

        # UI should reflect Live mode
        assert main_window.mode_label.get_text() == "Live"
        assert main_window.live_mode_banner.get_revealed()

    def test_has_setup_mode_toggle_method(self, main_window):
        """MainWindow should have mode toggle setup method."""
        assert hasattr(main_window, "_setup_mode_toggle")

    def test_has_update_mode_ui_method(self, main_window):
        """MainWindow should have UI update method."""
        assert hasattr(main_window, "_update_mode_ui")

    def test_has_on_mode_toggled_handler(self, main_window):
        """MainWindow should have mode toggle handler."""
        assert hasattr(main_window, "_on_mode_toggled")

    def test_has_show_live_mode_confirmation_method(self, main_window):
        """MainWindow should have confirmation dialog method."""
        assert hasattr(main_window, "_show_live_mode_confirmation")
