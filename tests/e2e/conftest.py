"""Pytest fixtures for E2E tests.

This module provides reusable fixtures for end-to-end testing of the HyprBind application.
Fixtures handle setup/teardown of headless display, temporary config files, and app instances.
"""
import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Tuple
from gi.repository import Adw

from tests.e2e.app_lifecycle import (
    setup_headless_display,
    launch_app,
    shutdown_app,
)


@pytest.fixture(scope="session")
def headless_display():
    """Configure GTK for headless operation using Broadway backend.

    This is a session-scoped fixture that sets up the headless display
    environment once for all tests in the session.

    The Broadway backend allows GTK4 applications to run without
    a physical display server (X11 or Wayland).
    """
    setup_headless_display()
    yield


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary Hyprland config file with sample bindings.

    This fixture creates a new temporary config file for each test,
    containing sample keybindings in the bindd format.

    Args:
        tmp_path: Pytest's built-in temporary directory fixture

    Yields:
        Path: Path to the temporary config file

    The file is automatically cleaned up after the test completes.
    """
    # Create temp config file with sample bindings
    config_file = tmp_path / "test_hyprland.conf"

    # Write sample config with bindd format bindings
    config_content = """# Test Hyprland Configuration
# Sample keybindings for E2E testing

# ======= Window Actions =======

bindd = $mainMod, RETURN, Opens terminal, exec, alacritty
bindd = $mainMod, Q, Close window, killactive,
bindd = $mainMod, V, Toggle floating, togglefloating,

# ======= Workspaces =======

bindd = $mainMod, 1, Switch to workspace 1, workspace, 1
bindd = $mainMod, 2, Switch to workspace 2, workspace, 2
"""

    config_file.write_text(config_content)
    yield config_file

    # Cleanup happens automatically via tmp_path


@pytest.fixture
def e2e_app(headless_display, temp_config_file) -> Tuple[Adw.Application, 'MainWindow']:
    """Launch application instance with temporary config.

    This fixture creates a fresh application instance for each test,
    configured with the temporary config file.

    Args:
        headless_display: Session fixture ensuring headless environment
        temp_config_file: Temporary config file for this test

    Yields:
        Tuple[Adw.Application, MainWindow]: Application and window instances

    The application is properly shut down after the test completes.
    """
    # Launch app with temp config
    app, window = launch_app(temp_config_file)

    yield app, window

    # Clean shutdown
    shutdown_app(app)


@pytest.fixture
def main_window(e2e_app) -> 'MainWindow':
    """Return the main window from the e2e_app fixture.

    This is a convenience fixture that extracts just the window
    from the e2e_app tuple for tests that only need the window.

    Args:
        e2e_app: The app/window tuple fixture

    Yields:
        MainWindow: The main application window
    """
    app, window = e2e_app
    yield window
