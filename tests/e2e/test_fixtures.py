"""Tests for E2E test fixtures.

This module validates that pytest fixtures are properly configured
and provide the expected test infrastructure.
"""
import os
import pytest
from pathlib import Path
from gi.repository import Adw


def test_headless_display_fixture(headless_display):
    """Test that headless display environment is configured."""
    # Verify Broadway backend is set
    assert os.environ.get('GDK_BACKEND') == 'broadway'
    assert os.environ.get('BROADWAY_DISPLAY') == ':5'

    # Verify messages are suppressed
    assert os.environ.get('G_MESSAGES_DEBUG') == ''


def test_temp_config_file_fixture(temp_config_file):
    """Test that temporary config file is created with sample bindings."""
    # Verify file exists
    assert temp_config_file.exists()
    assert temp_config_file.is_file()

    # Verify it's a temporary file
    assert str(temp_config_file).startswith('/tmp') or str(temp_config_file).startswith('/var/tmp')

    # Read and verify content
    content = temp_config_file.read_text()

    # Should contain bindd declarations
    assert 'bindd' in content

    # Should contain at least 2 sample bindings
    bindd_lines = [line for line in content.split('\n') if line.strip().startswith('bindd')]
    assert len(bindd_lines) >= 2

    # Verify bindd format: bindd = modifier, key, description, action, params
    for line in bindd_lines:
        parts = line.split(',')
        assert len(parts) >= 4, f"Invalid bindd format: {line}"


def test_e2e_app_fixture(e2e_app):
    """Test that e2e_app fixture launches application instance."""
    app, window = e2e_app

    # Verify app is an Adw.Application instance
    assert isinstance(app, Adw.Application)
    assert app.get_application_id() == "dev.hyprbind.e2e.test"

    # Verify window exists
    assert window is not None

    # Verify config_manager is configured with temp config
    assert hasattr(window, 'config_manager')
    assert window.config_manager.config_path is not None
    assert window.config_manager.config_path.exists()


def test_main_window_fixture(main_window):
    """Test that main_window fixture returns the main window."""
    # Verify window is not None
    assert main_window is not None

    # Verify it has required attributes
    assert hasattr(main_window, 'config_manager')
    assert hasattr(main_window, 'get_application')

    # Verify window has an application set
    app = main_window.get_application()
    assert app is not None
    assert isinstance(app, Adw.Application)
