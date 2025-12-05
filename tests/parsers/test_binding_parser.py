import pytest
from hyprbind.parsers.binding_parser import BindingParser
from hyprbind.core.models import BindType


def test_parse_bindd_simple():
    """Test parsing a simple bindd line."""
    line = "bindd = $mainMod, Q, Close window, killactive,"

    binding = BindingParser.parse_line(line, line_number=1)

    assert binding is not None
    assert binding.type == BindType.BINDD
    assert binding.modifiers == ["$mainMod"]
    assert binding.key == "Q"
    assert binding.description == "Close window"
    assert binding.action == "killactive"
    assert binding.params == ""


def test_parse_bindd_with_params():
    """Test parsing bindd with parameters."""
    line = "bindd = $mainMod, RETURN, Opens terminal, exec, alacritty"

    binding = BindingParser.parse_line(line, line_number=5)

    assert binding.action == "exec"
    assert binding.params == "alacritty"


def test_parse_bind_no_description():
    """Test parsing bind (no description field)."""
    line = "bind = $mainMod, V, togglefloating,"

    binding = BindingParser.parse_line(line, line_number=10)

    assert binding.type == BindType.BIND
    assert binding.description == ""
    assert binding.action == "togglefloating"


def test_parse_bindel():
    """Test parsing bindel (repeatable binding)."""
    line = "bindel = , XF86AudioRaiseVolume, exec, pactl set-sink-volume @DEFAULT_SINK@ +5%"

    binding = BindingParser.parse_line(line, line_number=15)

    assert binding.type == BindType.BINDEL
    assert binding.modifiers == []
    assert binding.key == "XF86AudioRaiseVolume"


def test_parse_bindm():
    """Test parsing bindm (mouse binding)."""
    line = "bindm = $mainMod, mouse:272, movewindow"

    binding = BindingParser.parse_line(line, line_number=20)

    assert binding.type == BindType.BINDM
    assert binding.key == "mouse:272"
    assert binding.action == "movewindow"


def test_parse_multiple_modifiers():
    """Test parsing binding with multiple modifiers."""
    line = "bindd = $mainMod SHIFT, Q, Force kill, exec, kill-window.sh"

    binding = BindingParser.parse_line(line, line_number=25)

    assert binding.modifiers == ["$mainMod", "SHIFT"]


def test_parse_code_keycode():
    """Test parsing binding with code:XXX format."""
    line = "bindd = , code:191, Screenshot area, exec, grimblast"

    binding = BindingParser.parse_line(line, line_number=30)

    assert binding.key == "code:191"


def test_parse_comment_line():
    """Test that comment lines return None."""
    line = "# This is a comment"

    binding = BindingParser.parse_line(line, line_number=1)

    assert binding is None


def test_parse_empty_line():
    """Test that empty lines return None."""
    line = "   "

    binding = BindingParser.parse_line(line, line_number=1)

    assert binding is None


def test_parse_invalid_line():
    """Test that invalid lines return None."""
    line = "some random text"

    binding = BindingParser.parse_line(line, line_number=1)

    assert binding is None
