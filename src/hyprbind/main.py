"""Main entry point for HyprBind application."""

import sys
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw

from hyprbind.ui.main_window import MainWindow


def main() -> int:
    """Run the HyprBind application."""
    app = Adw.Application(application_id="com.hyprbind.HyprBind")
    app.connect("activate", on_activate)
    return app.run(sys.argv)


def on_activate(app: Adw.Application) -> None:
    """Handle application activation."""
    window = MainWindow(application=app)
    window.present()


if __name__ == "__main__":
    sys.exit(main())
