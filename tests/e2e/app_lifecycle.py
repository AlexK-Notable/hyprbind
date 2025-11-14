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
    from hyprbind.core.config_manager import ConfigManager
    import time

    # Create application with unique ID to avoid conflicts between tests
    # Use timestamp to ensure uniqueness
    app_id = f"dev.hyprbind.e2e.test.{int(time.time() * 1000000)}"
    app = Adw.Application(application_id=app_id)

    # Register the application (emits startup signal)
    # This is required for dialogs to work properly
    app.register()

    # CRITICAL FIX: Monkey-patch ConfigManager.__init__ to use test config path
    # MainWindow creates ConfigManager in __init__ and immediately starts async loading,
    # so we need to inject the test path BEFORE MainWindow is created
    original_init = ConfigManager.__init__

    def patched_init(cm_self, cm_config_path=None):
        # Always use test config path, ignoring any passed argument
        original_init(cm_self, config_path=config_path)

    ConfigManager.__init__ = patched_init

    try:
        # Create main window (will now use test config path)
        window = MainWindow(application=app)

        # Verify the config path was set correctly
        assert window.config_manager.config_path == config_path, (
            f"Config path not set correctly! "
            f"Expected: {config_path}, Got: {window.config_manager.config_path}"
        )
    finally:
        # Restore original __init__ to avoid affecting other tests
        ConfigManager.__init__ = original_init

    return app, window


def shutdown_app(app: Adw.Application) -> None:
    """Gracefully shutdown application and cleanup GTK resources.

    Args:
        app: Application instance to shutdown
    """
    import time

    # Close all windows first
    windows = list(app.get_windows())
    for window in windows:
        window.close()

    # Process pending events to ensure windows are destroyed
    context = GLib.MainContext.default()
    for i in range(200):
        if context.pending():
            context.iteration(False)

    # Release the app (this unregisters from DBus)
    app.release()

    # Process more events and add small delay to ensure DBus unregistration completes
    for i in range(100):
        if context.pending():
            context.iteration(False)

    # Small sleep to ensure DBus cleanup completes
    time.sleep(0.05)


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
