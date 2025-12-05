"""Hyprland IPC client for live keybinding testing."""

import json
import os
import socket
from pathlib import Path
from typing import Any, Dict, Optional

from hyprbind.core.models import Binding


class HyprlandNotRunningError(Exception):
    """Raised when Hyprland is not running."""

    pass


class HyprlandConnectionError(Exception):
    """Raised when cannot connect to Hyprland IPC."""

    pass


class HyprlandClient:
    """Client for communicating with Hyprland via IPC socket."""

    def __init__(self) -> None:
        """Initialize the Hyprland IPC client."""
        self.socket_path: Optional[Path] = None
        self._socket: Optional[socket.socket] = None

    @staticmethod
    def is_running() -> bool:
        """
        Check if Hyprland is running.

        Returns:
            True if Hyprland is running and socket exists, False otherwise.
        """
        socket_path = HyprlandClient.get_socket_path()
        return socket_path is not None

    @staticmethod
    def get_socket_path() -> Optional[Path]:
        """
        Find Hyprland IPC socket path.

        Returns:
            Path to socket if found, None otherwise.
        """
        # Get Hyprland instance signature from environment
        signature = os.getenv("HYPRLAND_INSTANCE_SIGNATURE")
        if not signature:
            return None

        # Try XDG_RUNTIME_DIR first (preferred location)
        runtime_dir = os.getenv("XDG_RUNTIME_DIR")
        if runtime_dir:
            socket_path = Path(runtime_dir) / "hypr" / signature / ".socket.sock"
            if socket_path.exists():
                return socket_path

        # Fallback to /tmp
        socket_path = Path("/tmp/hypr") / signature / ".socket.sock"
        if socket_path.exists():
            return socket_path

        return None

    def connect(self) -> bool:
        """
        Connect to Hyprland IPC socket.

        Returns:
            True if connection successful.

        Raises:
            HyprlandNotRunningError: If Hyprland is not running.
            HyprlandConnectionError: If connection fails.
        """
        # Find socket path
        self.socket_path = self.get_socket_path()
        if self.socket_path is None:
            raise HyprlandNotRunningError(
                "Hyprland is not running or socket not found. "
                "Make sure HYPRLAND_INSTANCE_SIGNATURE environment variable is set."
            )

        # Create socket and connect
        try:
            self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._socket.connect(str(self.socket_path))
            return True
        except (ConnectionRefusedError, PermissionError, OSError) as e:
            raise HyprlandConnectionError(f"Failed to connect to Hyprland IPC: {e}")

    def send_command(self, command: str) -> Dict[str, Any]:
        """
        Send command to Hyprland and get response.

        Args:
            command: Command string to send.

        Returns:
            Parsed JSON response from Hyprland.

        Raises:
            HyprlandNotRunningError: If not connected.
            HyprlandConnectionError: If command fails or times out.
        """
        if self.socket_path is None:
            raise HyprlandNotRunningError(
                "Not connected to Hyprland. Call connect() first."
            )

        # Create a new socket for each command
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.settimeout(5.0)  # 5 second timeout
            sock.connect(str(self.socket_path))
            sock.sendall(command.encode())

            # Receive response
            response = sock.recv(4096).decode()

            # Parse JSON response if not empty
            if not response:
                return {}

            try:
                return json.loads(response)
            except json.JSONDecodeError as e:
                raise HyprlandConnectionError(f"Invalid response from Hyprland: {e}")

        except socket.timeout:
            raise HyprlandConnectionError("Connection timed out")
        except OSError as e:
            raise HyprlandConnectionError(f"Command failed: {e}")
        finally:
            sock.close()

    def add_binding(self, binding: Binding) -> bool:
        """
        Add keybinding via IPC.

        Args:
            binding: Binding to add.

        Returns:
            True if successful, False otherwise.
        """
        try:
            # Build modifier string
            mods = " ".join(binding.modifiers) if binding.modifiers else ""

            # Build command based on whether params exist
            if binding.params:
                command = f"keyword bind,{mods},{binding.key},{binding.action},{binding.params}"
            else:
                command = f"keyword bind,{mods},{binding.key},{binding.action}"

            # Send command
            self.send_command(command)
            return True

        except (HyprlandConnectionError, HyprlandNotRunningError):
            return False

    def remove_binding(self, binding: Binding) -> bool:
        """
        Remove keybinding via IPC.

        Args:
            binding: Binding to remove.

        Returns:
            True if successful, False otherwise.
        """
        try:
            # Build modifier string
            mods = " ".join(binding.modifiers) if binding.modifiers else ""

            # Build unbind command
            command = f"keyword unbind,{mods},{binding.key}"

            # Send command
            self.send_command(command)
            return True

        except (HyprlandConnectionError, HyprlandNotRunningError):
            return False

    def disconnect(self) -> None:
        """Close socket connection."""
        if self._socket is not None:
            self._socket.close()
            self._socket = None

    def __enter__(self) -> "HyprlandClient":
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.disconnect()
