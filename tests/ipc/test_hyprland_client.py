"""Tests for Hyprland IPC client."""

import json
import socket
from pathlib import Path
from unittest import mock

import pytest

from hyprbind.core.models import Binding, BindType
from hyprbind.ipc import HyprlandClient, HyprlandConnectionError, HyprlandNotRunningError


class TestHyprlandDetection:
    """Tests for Hyprland instance detection."""

    def test_is_running_when_hyprland_env_present_and_socket_exists(self):
        """Should return True when HYPRLAND_INSTANCE_SIGNATURE is set and socket exists."""
        with mock.patch("os.getenv") as mock_getenv:
            mock_getenv.return_value = "test_signature_123"

            with mock.patch("pathlib.Path.exists") as mock_exists:
                mock_exists.return_value = True

                assert HyprlandClient.is_running() is True

    def test_is_running_when_hyprland_env_missing(self):
        """Should return False when HYPRLAND_INSTANCE_SIGNATURE is not set."""
        with mock.patch("os.getenv") as mock_getenv:
            mock_getenv.return_value = None

            assert HyprlandClient.is_running() is False

    def test_is_running_when_socket_does_not_exist(self):
        """Should return False when socket file doesn't exist."""
        with mock.patch("os.getenv") as mock_getenv:
            mock_getenv.return_value = "test_signature_123"

            with mock.patch("pathlib.Path.exists") as mock_exists:
                mock_exists.return_value = False

                assert HyprlandClient.is_running() is False


class TestSocketPathDiscovery:
    """Tests for socket path discovery."""

    def test_get_socket_path_xdg_runtime_dir(self):
        """Should find socket in XDG_RUNTIME_DIR when available."""
        with mock.patch("os.getenv") as mock_getenv:

            def getenv_side_effect(key):
                if key == "HYPRLAND_INSTANCE_SIGNATURE":
                    return "test_sig"
                elif key == "XDG_RUNTIME_DIR":
                    return "/run/user/1000"
                return None

            mock_getenv.side_effect = getenv_side_effect

            with mock.patch("pathlib.Path.exists") as mock_exists:
                mock_exists.return_value = True

                path = HyprlandClient.get_socket_path()

                assert path is not None
                assert str(path) == "/run/user/1000/hypr/test_sig/.socket.sock"

    def test_get_socket_path_tmp_fallback(self):
        """Should fallback to /tmp when XDG_RUNTIME_DIR socket doesn't exist."""
        with mock.patch("os.getenv") as mock_getenv:

            def getenv_side_effect(key):
                if key == "HYPRLAND_INSTANCE_SIGNATURE":
                    return "test_sig"
                elif key == "XDG_RUNTIME_DIR":
                    return "/run/user/1000"
                return None

            mock_getenv.side_effect = getenv_side_effect

            with mock.patch("pathlib.Path.exists") as mock_exists:
                # First call (XDG) returns False, second call (/tmp) returns True
                mock_exists.side_effect = [False, True]

                path = HyprlandClient.get_socket_path()

                assert path is not None
                assert str(path) == "/tmp/hypr/test_sig/.socket.sock"

    def test_get_socket_path_no_signature(self):
        """Should return None when HYPRLAND_INSTANCE_SIGNATURE is not set."""
        with mock.patch("os.getenv") as mock_getenv:
            mock_getenv.return_value = None

            path = HyprlandClient.get_socket_path()

            assert path is None

    def test_get_socket_path_socket_not_found(self):
        """Should return None when socket doesn't exist in any location."""
        with mock.patch("os.getenv") as mock_getenv:

            def getenv_side_effect(key):
                if key == "HYPRLAND_INSTANCE_SIGNATURE":
                    return "test_sig"
                elif key == "XDG_RUNTIME_DIR":
                    return "/run/user/1000"
                return None

            mock_getenv.side_effect = getenv_side_effect

            with mock.patch("pathlib.Path.exists") as mock_exists:
                mock_exists.return_value = False

                path = HyprlandClient.get_socket_path()

                assert path is None


class TestConnection:
    """Tests for socket connection."""

    def test_connect_success(self):
        """Should successfully connect when socket is available."""
        client = HyprlandClient()

        with mock.patch.object(HyprlandClient, "get_socket_path") as mock_get_path:
            mock_get_path.return_value = Path("/tmp/hypr/test/.socket.sock")

            with mock.patch("socket.socket") as mock_socket_class:
                mock_socket_instance = mock.Mock()
                mock_socket_class.return_value = mock_socket_instance

                result = client.connect()

                assert result is True
                assert client.socket_path == Path("/tmp/hypr/test/.socket.sock")
                mock_socket_instance.connect.assert_called_once_with(
                    "/tmp/hypr/test/.socket.sock"
                )

    def test_connect_no_socket_path(self):
        """Should raise HyprlandNotRunningError when socket path not found."""
        client = HyprlandClient()

        with mock.patch.object(HyprlandClient, "get_socket_path") as mock_get_path:
            mock_get_path.return_value = None

            with pytest.raises(HyprlandNotRunningError) as exc_info:
                client.connect()

            assert "Hyprland is not running" in str(exc_info.value)

    def test_connect_connection_refused(self):
        """Should raise HyprlandConnectionError when connection is refused."""
        client = HyprlandClient()

        with mock.patch.object(HyprlandClient, "get_socket_path") as mock_get_path:
            mock_get_path.return_value = Path("/tmp/hypr/test/.socket.sock")

            with mock.patch("socket.socket") as mock_socket_class:
                mock_socket_instance = mock.Mock()
                mock_socket_class.return_value = mock_socket_instance
                mock_socket_instance.connect.side_effect = ConnectionRefusedError(
                    "Connection refused"
                )

                with pytest.raises(HyprlandConnectionError) as exc_info:
                    client.connect()

                assert "Failed to connect" in str(exc_info.value)

    def test_connect_permission_error(self):
        """Should raise HyprlandConnectionError on permission error."""
        client = HyprlandClient()

        with mock.patch.object(HyprlandClient, "get_socket_path") as mock_get_path:
            mock_get_path.return_value = Path("/tmp/hypr/test/.socket.sock")

            with mock.patch("socket.socket") as mock_socket_class:
                mock_socket_instance = mock.Mock()
                mock_socket_class.return_value = mock_socket_instance
                mock_socket_instance.connect.side_effect = PermissionError(
                    "Permission denied"
                )

                with pytest.raises(HyprlandConnectionError) as exc_info:
                    client.connect()

                assert "Failed to connect" in str(exc_info.value)


class TestCommandSending:
    """Tests for sending commands to Hyprland."""

    def test_send_command_success(self):
        """Should successfully send command and receive response."""
        client = HyprlandClient()
        client.socket_path = Path("/tmp/hypr/test/.socket.sock")

        response_data = {"ok": True, "status": "success"}
        response_bytes = json.dumps(response_data).encode()

        with mock.patch("socket.socket") as mock_socket_class:
            mock_socket_instance = mock.Mock()
            mock_socket_class.return_value = mock_socket_instance
            mock_socket_instance.recv.return_value = response_bytes

            result = client.send_command("keyword bind,SUPER,Q,killactive")

            assert result == response_data
            mock_socket_instance.connect.assert_called_once()
            mock_socket_instance.sendall.assert_called_once_with(
                b"keyword bind,SUPER,Q,killactive"
            )
            mock_socket_instance.close.assert_called_once()

    def test_send_command_empty_response(self):
        """Should handle empty response gracefully."""
        client = HyprlandClient()
        client.socket_path = Path("/tmp/hypr/test/.socket.sock")

        with mock.patch("socket.socket") as mock_socket_class:
            mock_socket_instance = mock.Mock()
            mock_socket_class.return_value = mock_socket_instance
            mock_socket_instance.recv.return_value = b""

            result = client.send_command("keyword bind,SUPER,Q,killactive")

            assert result == {}

    def test_send_command_json_parse_error(self):
        """Should handle invalid JSON response."""
        client = HyprlandClient()
        client.socket_path = Path("/tmp/hypr/test/.socket.sock")

        with mock.patch("socket.socket") as mock_socket_class:
            mock_socket_instance = mock.Mock()
            mock_socket_class.return_value = mock_socket_instance
            mock_socket_instance.recv.return_value = b"invalid json"

            with pytest.raises(HyprlandConnectionError) as exc_info:
                client.send_command("keyword bind,SUPER,Q,killactive")

            assert "Invalid response" in str(exc_info.value)

    def test_send_command_socket_error(self):
        """Should handle socket errors during send."""
        client = HyprlandClient()
        client.socket_path = Path("/tmp/hypr/test/.socket.sock")

        with mock.patch("socket.socket") as mock_socket_class:
            mock_socket_instance = mock.Mock()
            mock_socket_class.return_value = mock_socket_instance
            mock_socket_instance.sendall.side_effect = OSError("Socket error")

            with pytest.raises(HyprlandConnectionError) as exc_info:
                client.send_command("keyword bind,SUPER,Q,killactive")

            assert "Command failed" in str(exc_info.value)

    def test_send_command_without_socket_path(self):
        """Should raise error when socket_path is not set."""
        client = HyprlandClient()
        # socket_path is None

        with pytest.raises(HyprlandNotRunningError) as exc_info:
            client.send_command("keyword bind,SUPER,Q,killactive")

        assert "Not connected" in str(exc_info.value)


class TestBindingOperations:
    """Tests for add/remove binding operations."""

    def test_add_binding_success(self):
        """Should successfully add binding via IPC."""
        binding = Binding(
            type=BindType.BINDD,
            modifiers=["SUPER"],
            key="Q",
            description="Close window",
            action="killactive",
            params="",
            submap=None,
            line_number=1,
            category="Window Management",
        )

        client = HyprlandClient()
        client.socket_path = Path("/tmp/hypr/test/.socket.sock")

        with mock.patch.object(client, "send_command") as mock_send:
            mock_send.return_value = {"ok": True}

            result = client.add_binding(binding)

            assert result is True
            mock_send.assert_called_once_with("keyword bind,SUPER,Q,killactive")

    def test_add_binding_with_multiple_modifiers(self):
        """Should handle multiple modifiers correctly."""
        binding = Binding(
            type=BindType.BINDD,
            modifiers=["SUPER", "SHIFT"],
            key="Q",
            description="Close window",
            action="killactive",
            params="",
            submap=None,
            line_number=1,
            category="Window Management",
        )

        client = HyprlandClient()
        client.socket_path = Path("/tmp/hypr/test/.socket.sock")

        with mock.patch.object(client, "send_command") as mock_send:
            mock_send.return_value = {"ok": True}

            result = client.add_binding(binding)

            assert result is True
            mock_send.assert_called_once_with("keyword bind,SUPER SHIFT,Q,killactive")

    def test_add_binding_with_params(self):
        """Should include params in command when present."""
        binding = Binding(
            type=BindType.BINDD,
            modifiers=["SUPER"],
            key="1",
            description="Switch to workspace 1",
            action="workspace",
            params="1",
            submap=None,
            line_number=1,
            category="Workspaces",
        )

        client = HyprlandClient()
        client.socket_path = Path("/tmp/hypr/test/.socket.sock")

        with mock.patch.object(client, "send_command") as mock_send:
            mock_send.return_value = {"ok": True}

            result = client.add_binding(binding)

            assert result is True
            mock_send.assert_called_once_with("keyword bind,SUPER,1,workspace,1")

    def test_add_binding_failure(self):
        """Should return False when command fails."""
        binding = Binding(
            type=BindType.BINDD,
            modifiers=["SUPER"],
            key="Q",
            description="Close window",
            action="killactive",
            params="",
            submap=None,
            line_number=1,
            category="Window Management",
        )

        client = HyprlandClient()
        client.socket_path = Path("/tmp/hypr/test/.socket.sock")

        with mock.patch.object(client, "send_command") as mock_send:
            mock_send.side_effect = HyprlandConnectionError("Failed")

            result = client.add_binding(binding)

            assert result is False

    def test_remove_binding_success(self):
        """Should successfully remove binding via IPC."""
        binding = Binding(
            type=BindType.BINDD,
            modifiers=["SUPER"],
            key="Q",
            description="Close window",
            action="killactive",
            params="",
            submap=None,
            line_number=1,
            category="Window Management",
        )

        client = HyprlandClient()
        client.socket_path = Path("/tmp/hypr/test/.socket.sock")

        with mock.patch.object(client, "send_command") as mock_send:
            mock_send.return_value = {"ok": True}

            result = client.remove_binding(binding)

            assert result is True
            mock_send.assert_called_once_with("keyword unbind,SUPER,Q")

    def test_remove_binding_with_multiple_modifiers(self):
        """Should handle multiple modifiers in unbind."""
        binding = Binding(
            type=BindType.BINDD,
            modifiers=["SUPER", "SHIFT"],
            key="Q",
            description="Close window",
            action="killactive",
            params="",
            submap=None,
            line_number=1,
            category="Window Management",
        )

        client = HyprlandClient()
        client.socket_path = Path("/tmp/hypr/test/.socket.sock")

        with mock.patch.object(client, "send_command") as mock_send:
            mock_send.return_value = {"ok": True}

            result = client.remove_binding(binding)

            assert result is True
            mock_send.assert_called_once_with("keyword unbind,SUPER SHIFT,Q")

    def test_remove_binding_failure(self):
        """Should return False when unbind fails."""
        binding = Binding(
            type=BindType.BINDD,
            modifiers=["SUPER"],
            key="Q",
            description="Close window",
            action="killactive",
            params="",
            submap=None,
            line_number=1,
            category="Window Management",
        )

        client = HyprlandClient()
        client.socket_path = Path("/tmp/hypr/test/.socket.sock")

        with mock.patch.object(client, "send_command") as mock_send:
            mock_send.side_effect = HyprlandConnectionError("Failed")

            result = client.remove_binding(binding)

            assert result is False


class TestDisconnect:
    """Tests for disconnecting from Hyprland."""

    def test_disconnect_closes_socket(self):
        """Should close socket on disconnect."""
        client = HyprlandClient()
        mock_socket = mock.Mock()
        client._socket = mock_socket

        client.disconnect()

        mock_socket.close.assert_called_once()
        assert client._socket is None

    def test_disconnect_without_socket(self):
        """Should handle disconnect when no socket is active."""
        client = HyprlandClient()
        # No socket set

        # Should not raise any errors
        client.disconnect()

        assert client._socket is None


class TestContextManager:
    """Tests for using HyprlandClient as context manager."""

    def test_context_manager_connects_and_disconnects(self):
        """Should connect on enter and disconnect on exit."""
        with mock.patch.object(HyprlandClient, "get_socket_path") as mock_get_path:
            mock_get_path.return_value = Path("/tmp/hypr/test/.socket.sock")

            with mock.patch("socket.socket") as mock_socket_class:
                mock_socket_instance = mock.Mock()
                mock_socket_class.return_value = mock_socket_instance

                with HyprlandClient() as client:
                    assert client.socket_path is not None

                # Socket should be closed after exiting context
                mock_socket_instance.close.assert_called()

    def test_context_manager_handles_exceptions(self):
        """Should disconnect even if exception occurs."""
        with mock.patch.object(HyprlandClient, "get_socket_path") as mock_get_path:
            mock_get_path.return_value = Path("/tmp/hypr/test/.socket.sock")

            with mock.patch("socket.socket") as mock_socket_class:
                mock_socket_instance = mock.Mock()
                mock_socket_class.return_value = mock_socket_instance

                try:
                    with HyprlandClient() as client:
                        raise ValueError("Test exception")
                except ValueError:
                    pass

                # Socket should still be closed
                mock_socket_instance.close.assert_called()
