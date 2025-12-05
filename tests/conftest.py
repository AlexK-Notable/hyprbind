"""Shared test fixtures for HyprBind tests."""

import pytest
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw
from unittest.mock import MagicMock

from hyprbind.core.config_manager import ConfigManager, OperationResult
from hyprbind.core.mode_manager import ModeManager
from hyprbind.core.models import Config, Category


@pytest.fixture
def config_manager():
    """Create ConfigManager for testing."""
    manager = ConfigManager()
    manager.config = Config()
    manager.config.categories = {
        "Applications": Category(name="Applications"),
        "Window Management": Category(name="Window Management"),
    }
    # Mock save method
    manager.save = MagicMock(return_value=OperationResult(success=True))
    return manager


@pytest.fixture
def mode_manager(config_manager):
    """Create ModeManager for testing."""
    return ModeManager(config_manager)
