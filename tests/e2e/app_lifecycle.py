"""Application lifecycle management for E2E tests."""
import os
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib
from pathlib import Path
from typing import Tuple
from contextlib import contextmanager


def setup_headless_display() -> None:
    """Configure GTK for headless operation using Broadway backend.

    Broadway is GTK4's HTML5 backend that doesn't require a display server.
    This allows tests to run without X11 or Wayland.
    """
    os.environ['GDK_BACKEND'] = 'broadway'
    os.environ['BROADWAY_DISPLAY'] = ':5'

    # Suppress GTK warnings in headless mode
    os.environ['G_MESSAGES_DEBUG'] = ''


def launch_app(config_path: Path) -> Tuple[Adw.Application, 'MainWindow']:
    """Launch application without blocking event loop.

    Args:
        config_path: Path to Hyprland config file for testing

    Returns:
        Tuple of (application, main_window)
    """
    from hyprbind.ui.main_window import MainWindow

    # Create application
    app = Adw.Application(application_id="dev.hyprbind.e2e.test")

    # Create main window with test config
    window = MainWindow(application=app)
    window.config_manager.config_path = config_path

    return app, window


def shutdown_app(app: Adw.Application) -> None:
    """Gracefully shutdown application and cleanup GTK resources.

    Args:
        app: Application instance to shutdown
    """
    # Close all windows
    for window in app.get_windows():
        window.close()

    # Process remaining events
    context = GLib.MainContext.default()
    while context.pending():
        context.iteration(False)

    # Quit application
    app.quit()


@contextmanager
def ApplicationContext(config_path: Path):
    """Context manager for application lifecycle.

    Ensures proper cleanup even if test fails.

    Args:
        config_path: Path to test config file

    Yields:
        Tuple of (application, main_window)
    """
    setup_headless_display()
    app, window = launch_app(config_path)

    try:
        yield app, window
    finally:
        shutdown_app(app)
