"""Hyprland IPC client for live keybinding testing."""

from .hyprland_client import (
    HyprlandClient,
    HyprlandConnectionError,
    HyprlandNotRunningError,
)

__all__ = [
    "HyprlandClient",
    "HyprlandConnectionError",
    "HyprlandNotRunningError",
]
