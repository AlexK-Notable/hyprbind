import pytest
from pathlib import Path
from hyprbind.parsers.config_parser import ConfigParser
from hyprbind.core.models import Config, BindType


def test_parse_config_file():
    """Test parsing complete config file."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "sample_keybinds.conf"

    config = ConfigParser.parse_file(fixture_path, skip_validation=True)

    assert config is not None
    assert len(config.get_all_bindings()) > 0


def test_parse_config_categorizes_bindings():
    """Test that bindings are properly categorized."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "sample_keybinds.conf"

    config = ConfigParser.parse_file(fixture_path, skip_validation=True)

    # Should have Window Actions category
    assert "Window Actions" in config.categories
    # Should have Workspaces category
    assert "Workspaces" in config.categories


def test_parse_config_preserves_line_numbers():
    """Test that line numbers are tracked."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "sample_keybinds.conf"

    config = ConfigParser.parse_file(fixture_path, skip_validation=True)

    bindings = config.get_all_bindings()
    # All bindings should have line numbers
    assert all(b.line_number > 0 for b in bindings)


def test_parse_string():
    """Test parsing from string."""
    content = """
# ======= Test Category =======
bindd = $mainMod, Q, Close, killactive,
bindd = $mainMod, V, Float, togglefloating,
"""

    config = ConfigParser.parse_string(content)

    assert len(config.get_all_bindings()) == 2
    assert "Test Category" in config.categories


def test_parse_empty_file():
    """Test parsing empty config."""
    config = ConfigParser.parse_string("")

    assert len(config.get_all_bindings()) == 0


def test_parse_nonexistent_file():
    """Test handling of non-existent config file."""
    non_existent = Path("/tmp/nonexistent_hyprbind_test_12345.conf")

    config = ConfigParser.parse_file(non_existent, skip_validation=True)

    assert len(config.get_all_bindings()) == 0
    assert config.file_path == str(non_existent)
    assert config.original_content == ""


def test_parse_file_loads_variables():
    """Test that variables are loaded from config directory."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "sample_keybinds.conf"

    config = ConfigParser.parse_file(fixture_path, skip_validation=True)

    # Variables should be loaded from variables.conf and defaults.conf in fixtures dir
    assert isinstance(config.variables, dict)
    # The fixture directory should have some variables defined
    assert len(config.variables) > 0
