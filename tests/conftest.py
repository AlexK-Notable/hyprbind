"""Shared test fixtures for HyprBind tests."""

import pytest
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw
from unittest.mock import MagicMock
from pathlib import Path

from hyprbind.core.config_manager import ConfigManager, OperationResult
from hyprbind.core.mode_manager import ModeManager
from hyprbind.core.models import Config, Category


@pytest.fixture
def config_manager(tmp_path):
    """Create ConfigManager for testing with isolated temp path.

    CRITICAL: Uses tmp_path to ensure tests NEVER write to user's real config.
    """
    # Create temp config file
    temp_config = tmp_path / "test_keybinds.conf"
    temp_config.write_text("# Test config - isolated from real user config\n")

    # Create manager with temp path and skip_validation
    manager = ConfigManager(config_path=temp_config, skip_validation=True)
    manager.config = Config()
    manager.config.categories = {
        "Applications": Category(name="Applications"),
        "Window Management": Category(name="Window Management"),
    }
    # Mock save method as additional safety layer
    manager.save = MagicMock(return_value=OperationResult(success=True))
    return manager


@pytest.fixture
def mode_manager(config_manager):
    """Create ModeManager for testing."""
    return ModeManager(config_manager)
