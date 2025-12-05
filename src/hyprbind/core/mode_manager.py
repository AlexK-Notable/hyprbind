"""Mode manager for Safe/Live toggle functionality."""

from enum import Enum
from typing import Optional

from hyprbind.core.config_manager import ConfigManager, OperationResult
from hyprbind.core.models import Binding


class Mode(Enum):
    """Operating modes for HyprBind."""

    SAFE = "safe"  # File-only changes, requires reload
    LIVE = "live"  # IPC changes, immediate testing


class ModeManager:
    """Manages Safe/Live mode toggle for keybinding operations."""

    def __init__(self, config_manager: ConfigManager):
        """
        Initialize ModeManager.

        Args:
            config_manager: ConfigManager instance for Safe mode operations
        """
        self.config_manager = config_manager
        self.current_mode = Mode.SAFE
        self._hyprland_client: Optional["HyprlandClient"] = None

    def get_mode(self) -> Mode:
        """
        Get current operating mode.

        Returns:
            Current Mode (SAFE or LIVE)
        """
        return self.current_mode

    def set_mode(self, mode: Mode) -> bool:
        """
        Set operating mode.

        Args:
            mode: Mode to switch to (SAFE or LIVE)

        Returns:
            True if mode was set successfully, False if mode is unavailable
        """
        # Check if LIVE mode is available before switching
        if mode == Mode.LIVE and not self.is_live_available():
            return False

        self.current_mode = mode
        return True

    def is_live_available(self) -> bool:
        """
        Check if Live mode is available (Hyprland running).

        Returns:
            True if Hyprland is running and IPC is available
        """
        from hyprbind.ipc.hyprland_client import HyprlandClient

        return HyprlandClient.is_running()

    def apply_binding(self, binding: Binding, action: str) -> Optional[OperationResult]:
        """
        Apply binding change based on current mode.

        Args:
            binding: Binding to apply
            action: "add" or "remove"

        Returns:
            OperationResult with success status, or None for invalid action
        """
        if action not in ("add", "remove"):
            # Invalid action - return None
            return None

        if self.current_mode == Mode.SAFE:
            return self._apply_safe(binding, action)
        else:
            return self._apply_live(binding, action)

    def _apply_safe(self, binding: Binding, action: str) -> OperationResult:
        """
        Apply binding in Safe mode (file only).

        Args:
            binding: Binding to apply
            action: "add" or "remove"

        Returns:
            OperationResult from config_manager
        """
        if action == "add":
            return self.config_manager.add_binding(binding)
        elif action == "remove":
            return self.config_manager.remove_binding(binding)

    def _apply_live(self, binding: Binding, action: str) -> OperationResult:
        """
        Apply binding in Live mode (IPC only, no file write).

        Args:
            binding: Binding to apply
            action: "add" or "remove"

        Returns:
            OperationResult with IPC operation status
        """
        from hyprbind.ipc.hyprland_client import HyprlandClient

        # Create client if not exists
        if not self._hyprland_client:
            self._hyprland_client = HyprlandClient()
            if not self._hyprland_client.connect():
                return OperationResult(
                    success=False, message="Failed to connect to Hyprland"
                )

        try:
            # Execute IPC command
            if action == "add":
                success = self._hyprland_client.add_binding(binding)
            elif action == "remove":
                success = self._hyprland_client.remove_binding(binding)
            else:
                return OperationResult(success=False, message="Invalid action")

            if success:
                return OperationResult(
                    success=True,
                    message=f"Binding {action}ed via IPC (not saved to file)",
                )
            else:
                return OperationResult(success=False, message="IPC command failed")

        except Exception as e:
            return OperationResult(success=False, message=f"IPC error: {e}")
