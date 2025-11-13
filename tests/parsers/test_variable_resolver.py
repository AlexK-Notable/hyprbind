import pytest
from pathlib import Path
from hyprbind.parsers.variable_resolver import VariableResolver


def test_load_variables_from_file():
    """Test loading variables from config file."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "defaults.conf"

    variables = VariableResolver.load_from_file(fixture_path)

    assert variables["$terminal"] == "alacritty"
    assert variables["$filemanager"] == "nemo"
    assert variables["$browser"] == "firefox"


def test_resolve_simple_variable():
    """Test resolving a simple variable."""
    variables = {"$terminal": "alacritty"}

    result = VariableResolver.resolve("$terminal", variables)

    assert result == "alacritty"


def test_resolve_no_variable():
    """Test resolving string with no variables."""
    variables = {"$terminal": "alacritty"}

    result = VariableResolver.resolve("thunar", variables)

    assert result == "thunar"


def test_resolve_multiple_variables():
    """Test resolving string with multiple variables."""
    variables = {
        "$terminal": "alacritty",
        "$editor": "nvim",
    }

    result = VariableResolver.resolve("$terminal -e $editor", variables)

    assert result == "alacritty -e nvim"


def test_load_all_variables():
    """Test loading from multiple config files."""
    fixture_dir = Path(__file__).parent.parent / "fixtures"

    variables = VariableResolver.load_all_variables(fixture_dir)

    # From defaults.conf
    assert variables["$terminal"] == "alacritty"
    # From variables.conf
    assert variables["$mainMod"] == "SUPER"
    assert variables["$shot-region"] == "grimblast copysave area"
