"""Tests for mode manager (Safe/Live toggle)."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from hyprbind.core.mode_manager import ModeManager, Mode
from hyprbind.core.config_manager import ConfigManager, OperationResult
from hyprbind.core.models import Binding, BindType


@pytest.fixture
def mock_config_manager():
    """Create mock ConfigManager."""
    config_manager = Mock(spec=ConfigManager)
    # Mock successful operations by default
    config_manager.add_binding.return_value = OperationResult(success=True)
    config_manager.remove_binding.return_value = OperationResult(success=True)
    return config_manager


@pytest.fixture
def sample_binding():
    """Create sample binding for tests."""
    return Binding(
        type=BindType.BINDD,
        modifiers=["$mainMod"],
        key="Q",
        description="Close active window",
        action="killactive",
        params="",
        submap=None,
        line_number=1,
        category="Window Management",
    )


class TestModeEnum:
    """Test Mode enum."""

    def test_mode_enum_values(self):
        """Mode enum should have SAFE and LIVE values."""
        assert Mode.SAFE.value == "safe"
        assert Mode.LIVE.value == "live"


class TestModeManagerInitialization:
    """Test ModeManager initialization."""

    def test_init_defaults_to_safe_mode(self, mock_config_manager):
        """ModeManager should default to Safe mode."""
        manager = ModeManager(mock_config_manager)
        assert manager.get_mode() == Mode.SAFE

    def test_init_stores_config_manager(self, mock_config_manager):
        """ModeManager should store config manager reference."""
        manager = ModeManager(mock_config_manager)
        assert manager.config_manager is mock_config_manager

    def test_init_hyprland_client_none(self, mock_config_manager):
        """HyprlandClient should be None until needed."""
        manager = ModeManager(mock_config_manager)
        assert manager._hyprland_client is None


class TestModeGetting:
    """Test getting current mode."""

    def test_get_mode_returns_safe_by_default(self, mock_config_manager):
        """get_mode() should return SAFE by default."""
        manager = ModeManager(mock_config_manager)
        assert manager.get_mode() == Mode.SAFE


class TestModeSwitching:
    """Test switching between modes."""

    def test_set_mode_to_safe(self, mock_config_manager):
        """Should be able to set mode to SAFE."""
        manager = ModeManager(mock_config_manager)
        result = manager.set_mode(Mode.SAFE)
        assert result is True
        assert manager.get_mode() == Mode.SAFE

    @patch("hyprbind.ipc.hyprland_client.HyprlandClient")
    def test_set_mode_to_live_when_available(
        self, mock_client_class, mock_config_manager
    ):
        """Should set mode to LIVE when Hyprland is running."""
        # Mock Hyprland as running
        mock_client_class.is_running.return_value = True

        manager = ModeManager(mock_config_manager)
        result = manager.set_mode(Mode.LIVE)

        assert result is True
        assert manager.get_mode() == Mode.LIVE

    @patch("hyprbind.ipc.hyprland_client.HyprlandClient")
    def test_set_mode_to_live_when_unavailable(
        self, mock_client_class, mock_config_manager
    ):
        """Should fail to set LIVE mode when Hyprland not running."""
        # Mock Hyprland as not running
        mock_client_class.is_running.return_value = False

        manager = ModeManager(mock_config_manager)
        result = manager.set_mode(Mode.LIVE)

        assert result is False
        assert manager.get_mode() == Mode.SAFE  # Should stay in SAFE

    def test_switch_from_live_to_safe(self, mock_config_manager):
        """Should be able to switch from LIVE back to SAFE."""
        manager = ModeManager(mock_config_manager)

        # Force mode to LIVE (bypassing availability check for test)
        manager.current_mode = Mode.LIVE

        result = manager.set_mode(Mode.SAFE)
        assert result is True
        assert manager.get_mode() == Mode.SAFE


class TestLiveModeAvailability:
    """Test checking if Live mode is available."""

    @patch("hyprbind.ipc.hyprland_client.HyprlandClient")
    def test_is_live_available_when_running(
        self, mock_client_class, mock_config_manager
    ):
        """is_live_available() should return True when Hyprland running."""
        mock_client_class.is_running.return_value = True

        manager = ModeManager(mock_config_manager)
        assert manager.is_live_available() is True

    @patch("hyprbind.ipc.hyprland_client.HyprlandClient")
    def test_is_live_available_when_not_running(
        self, mock_client_class, mock_config_manager
    ):
        """is_live_available() should return False when Hyprland not running."""
        mock_client_class.is_running.return_value = False

        manager = ModeManager(mock_config_manager)
        assert manager.is_live_available() is False


class TestApplyBindingInSafeMode:
    """Test applying bindings in Safe mode."""

    def test_apply_binding_add_in_safe_mode(
        self, mock_config_manager, sample_binding
    ):
        """Adding binding in Safe mode should call config_manager.add_binding()."""
        manager = ModeManager(mock_config_manager)
        manager.set_mode(Mode.SAFE)

        result = manager.apply_binding(sample_binding, "add")

        assert result.success is True
        mock_config_manager.add_binding.assert_called_once_with(sample_binding)
        mock_config_manager.remove_binding.assert_not_called()

    def test_apply_binding_remove_in_safe_mode(
        self, mock_config_manager, sample_binding
    ):
        """Removing binding in Safe mode should call config_manager.remove_binding()."""
        manager = ModeManager(mock_config_manager)
        manager.set_mode(Mode.SAFE)

        result = manager.apply_binding(sample_binding, "remove")

        assert result.success is True
        mock_config_manager.remove_binding.assert_called_once_with(sample_binding)
        mock_config_manager.add_binding.assert_not_called()

    def test_apply_binding_safe_mode_failure(
        self, mock_config_manager, sample_binding
    ):
        """Safe mode should propagate failures from config_manager."""
        mock_config_manager.add_binding.return_value = OperationResult(
            success=False, message="Conflict detected"
        )

        manager = ModeManager(mock_config_manager)
        result = manager.apply_binding(sample_binding, "add")

        assert result.success is False
        assert "Conflict detected" in result.message


class TestApplyBindingInLiveMode:
    """Test applying bindings in Live mode."""

    @patch("hyprbind.ipc.hyprland_client.HyprlandClient")
    def test_apply_binding_add_in_live_mode(
        self, mock_client_class, mock_config_manager, sample_binding
    ):
        """Adding binding in Live mode should use IPC, not file write."""
        # Setup mocks
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.add_binding.return_value = True
        mock_client_class.return_value = mock_client
        mock_client_class.is_running.return_value = True

        manager = ModeManager(mock_config_manager)
        manager.set_mode(Mode.LIVE)

        result = manager.apply_binding(sample_binding, "add")

        # Should use IPC, not config_manager
        assert result.success is True
        assert "IPC" in result.message or "not saved" in result.message
        mock_client.connect.assert_called_once()
        mock_client.add_binding.assert_called_once_with(sample_binding)
        mock_config_manager.add_binding.assert_not_called()

    @patch("hyprbind.ipc.hyprland_client.HyprlandClient")
    def test_apply_binding_remove_in_live_mode(
        self, mock_client_class, mock_config_manager, sample_binding
    ):
        """Removing binding in Live mode should use IPC, not file write."""
        # Setup mocks
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.remove_binding.return_value = True
        mock_client_class.return_value = mock_client
        mock_client_class.is_running.return_value = True

        manager = ModeManager(mock_config_manager)
        manager.set_mode(Mode.LIVE)

        result = manager.apply_binding(sample_binding, "remove")

        # Should use IPC, not config_manager
        assert result.success is True
        mock_client.remove_binding.assert_called_once_with(sample_binding)
        mock_config_manager.remove_binding.assert_not_called()

    @patch("hyprbind.ipc.hyprland_client.HyprlandClient")
    def test_live_mode_connection_failure(
        self, mock_client_class, mock_config_manager, sample_binding
    ):
        """Live mode should handle IPC connection failures."""
        # Setup mocks
        mock_client = MagicMock()
        mock_client.connect.return_value = False
        mock_client_class.return_value = mock_client
        mock_client_class.is_running.return_value = True

        manager = ModeManager(mock_config_manager)
        manager.set_mode(Mode.LIVE)

        result = manager.apply_binding(sample_binding, "add")

        assert result.success is False
        assert "Failed to connect" in result.message

    @patch("hyprbind.ipc.hyprland_client.HyprlandClient")
    def test_live_mode_ipc_command_failure(
        self, mock_client_class, mock_config_manager, sample_binding
    ):
        """Live mode should handle IPC command failures."""
        # Setup mocks
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.add_binding.return_value = False  # Command fails
        mock_client_class.return_value = mock_client
        mock_client_class.is_running.return_value = True

        manager = ModeManager(mock_config_manager)
        manager.set_mode(Mode.LIVE)

        result = manager.apply_binding(sample_binding, "add")

        assert result.success is False
        assert "IPC command failed" in result.message

    @patch("hyprbind.ipc.hyprland_client.HyprlandClient")
    def test_live_mode_reuses_client(
        self, mock_client_class, mock_config_manager, sample_binding
    ):
        """Live mode should reuse HyprlandClient instance."""
        # Setup mocks
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.add_binding.return_value = True
        mock_client_class.return_value = mock_client
        mock_client_class.is_running.return_value = True

        manager = ModeManager(mock_config_manager)
        manager.set_mode(Mode.LIVE)

        # Apply two bindings
        manager.apply_binding(sample_binding, "add")
        manager.apply_binding(sample_binding, "remove")

        # Should only create client once and connect once
        assert mock_client_class.call_count == 1
        assert mock_client.connect.call_count == 1

    @patch("hyprbind.ipc.hyprland_client.HyprlandClient")
    def test_live_mode_exception_handling(
        self, mock_client_class, mock_config_manager, sample_binding
    ):
        """Live mode should handle exceptions gracefully."""
        # Setup mocks
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.add_binding.side_effect = Exception("IPC socket error")
        mock_client_class.return_value = mock_client
        mock_client_class.is_running.return_value = True

        manager = ModeManager(mock_config_manager)
        manager.set_mode(Mode.LIVE)

        result = manager.apply_binding(sample_binding, "add")

        assert result.success is False
        assert "IPC error" in result.message
        assert "socket error" in result.message


class TestInvalidAction:
    """Test handling of invalid actions."""

    def test_invalid_action_in_safe_mode(
        self, mock_config_manager, sample_binding
    ):
        """Invalid action in Safe mode should return None or handle gracefully."""
        manager = ModeManager(mock_config_manager)

        # This should either return None or an error result
        result = manager.apply_binding(sample_binding, "invalid_action")

        # Should not call any config_manager methods
        mock_config_manager.add_binding.assert_not_called()
        mock_config_manager.remove_binding.assert_not_called()

    @patch("hyprbind.ipc.hyprland_client.HyprlandClient")
    def test_invalid_action_in_live_mode(
        self, mock_client_class, mock_config_manager, sample_binding
    ):
        """Invalid action in Live mode should handle gracefully."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client_class.return_value = mock_client
        mock_client_class.is_running.return_value = True

        manager = ModeManager(mock_config_manager)
        manager.set_mode(Mode.LIVE)

        # This should either return None or an error result
        result = manager.apply_binding(sample_binding, "invalid_action")

        # Should not call any IPC methods
        mock_client.add_binding.assert_not_called()
        mock_client.remove_binding.assert_not_called()
