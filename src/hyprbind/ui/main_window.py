"""Main application window."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw
from pathlib import Path


# Get project root: __file__ -> ui/ -> hyprbind/ -> src/ -> dev/
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
_UI_FILE = _PROJECT_ROOT / "data" / "ui" / "main_window.ui"


@Gtk.Template(filename=str(_UI_FILE))
class MainWindow(Adw.ApplicationWindow):
    """Main HyprBind application window.

    This window uses GTK Builder template for UI definition.
    """

    __gtype_name__ = "HyprBindMainWindow"

    # Template children
    main_content = Gtk.Template.Child()
    header_bar = Gtk.Template.Child()
    placeholder_label = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
