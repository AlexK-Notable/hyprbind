"""Main application window."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw
from pathlib import Path
from typing import Any
import sys


def _get_ui_file_path() -> Path:
    """
    Get path to UI file, works both in development and when installed.

    Returns:
        Path to main_window.ui file
    """
    # Try development path first (for running from git repo)
    dev_path = Path(__file__).parent.parent.parent.parent / "data" / "ui" / "main_window.ui"
    if dev_path.exists():
        return dev_path

    # Try installed package data path
    try:
        from importlib.resources import files
        ui_file = files("hyprbind").parent / "data" / "ui" / "main_window.ui"
        if ui_file.exists():
            return ui_file
    except (ImportError, AttributeError):
        pass

    # Fallback: check common installation locations
    possible_paths = [
        Path(sys.prefix) / "share" / "hyprbind" / "ui" / "main_window.ui",
        Path.home() / ".local" / "share" / "hyprbind" / "ui" / "main_window.ui",
    ]

    for path in possible_paths:
        if path.exists():
            return path

    # If all else fails, return dev path and let it fail with clear error
    raise FileNotFoundError(
        f"Could not find main_window.ui. Tried:\n"
        f"  - Development: {dev_path}\n"
        f"  - Package data: <importlib.resources>\n"
        f"  - System: {possible_paths}\n"
        f"Please ensure the package is properly installed or run from git repository."
    )


_UI_FILE = _get_ui_file_path()


@Gtk.Template(filename=str(_UI_FILE))
class MainWindow(Adw.ApplicationWindow):
    """Main HyprBind application window.

    This window uses GTK Builder template for UI definition.
    """

    __gtype_name__ = "HyprBindMainWindow"

    # Template children with type annotations
    main_content: Gtk.Box = Gtk.Template.Child()
    header_bar: Adw.HeaderBar = Gtk.Template.Child()
    placeholder_label: Gtk.Label = Gtk.Template.Child()

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the main window."""
        super().__init__(**kwargs)
