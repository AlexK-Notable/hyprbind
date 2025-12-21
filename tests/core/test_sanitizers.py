"""Tests for core/sanitizers.py module."""

import pytest
from unittest.mock import MagicMock

from hyprbind.core.sanitizers import IPCSanitizer, CONTROL_CHARS


class TestControlCharsPattern:
    """Test the CONTROL_CHARS regex pattern."""

    def test_matches_null_byte(self):
        assert CONTROL_CHARS.search("\x00")

    def test_matches_newline(self):
        assert CONTROL_CHARS.search("\n")
        assert CONTROL_CHARS.search("\r")

    def test_matches_tab(self):
        assert CONTROL_CHARS.search("\t")

    def test_matches_del(self):
        assert CONTROL_CHARS.search("\x7f")

    def test_no_match_normal_chars(self):
        assert not CONTROL_CHARS.search("hello world")
        assert not CONTROL_CHARS.search("SUPER + Return")
        assert not CONTROL_CHARS.search("exec, kitty")

    def test_no_match_unicode(self):
        assert not CONTROL_CHARS.search("Launch Terminal 🚀")
        assert not CONTROL_CHARS.search("日本語")


class TestIPCSanitizerSanitize:
    """Test IPCSanitizer.sanitize method."""

    def test_removes_null_bytes(self):
        assert IPCSanitizer.sanitize("hello\x00world") == "helloworld"

    def test_removes_newlines(self):
        assert IPCSanitizer.sanitize("line1\nline2") == "line1line2"
        assert IPCSanitizer.sanitize("line1\r\nline2") == "line1line2"

    def test_removes_tabs(self):
        assert IPCSanitizer.sanitize("col1\tcol2") == "col1col2"

    def test_removes_del(self):
        assert IPCSanitizer.sanitize("text\x7fhere") == "texthere"

    def test_preserves_normal_chars(self):
        normal = "SUPER + Return, exec, kitty --title Terminal"
        assert IPCSanitizer.sanitize(normal) == normal

    def test_preserves_unicode(self):
        # Users might have unicode in descriptions
        assert IPCSanitizer.sanitize("Launch 🚀 terminal") == "Launch 🚀 terminal"
        assert IPCSanitizer.sanitize("日本語テスト") == "日本語テスト"

    def test_empty_string(self):
        assert IPCSanitizer.sanitize("") == ""

    def test_only_control_chars(self):
        assert IPCSanitizer.sanitize("\x00\n\r\t") == ""


class TestIPCSanitizerValidate:
    """Test IPCSanitizer.validate method."""

    def test_returns_error_for_null_byte(self):
        result = IPCSanitizer.validate("bad\x00input", "Key")
        assert result is not None
        assert "Key" in result
        assert "control characters" in result

    def test_returns_error_for_newline(self):
        result = IPCSanitizer.validate("bad\ninput", "Action")
        assert result is not None
        assert "Action" in result

    def test_returns_none_for_valid_input(self):
        assert IPCSanitizer.validate("SUPER", "Modifier") is None
        assert IPCSanitizer.validate("exec", "Action") is None
        assert IPCSanitizer.validate("kitty --title Test", "Params") is None

    def test_empty_string_is_valid(self):
        assert IPCSanitizer.validate("", "Field") is None

    def test_unicode_is_valid(self):
        assert IPCSanitizer.validate("🚀 Launch", "Description") is None


class TestIPCSanitizerValidateBinding:
    """Test IPCSanitizer.validate_binding method."""

    @pytest.fixture
    def mock_binding(self):
        """Create a mock binding for testing."""
        binding = MagicMock()
        binding.key = "Return"
        binding.action = "exec"
        binding.params = "kitty"
        binding.description = "Open terminal"
        binding.modifiers = ["SUPER", "SHIFT"]
        return binding

    def test_valid_binding_returns_none(self, mock_binding):
        result = IPCSanitizer.validate_binding(mock_binding)
        assert result is None

    def test_invalid_key_returns_error(self, mock_binding):
        mock_binding.key = "Return\x00"
        result = IPCSanitizer.validate_binding(mock_binding)
        assert result is not None
        assert "Key" in result

    def test_invalid_action_returns_error(self, mock_binding):
        mock_binding.action = "exec\n"
        result = IPCSanitizer.validate_binding(mock_binding)
        assert result is not None
        assert "Action" in result

    def test_invalid_params_returns_error(self, mock_binding):
        mock_binding.params = "kitty\x7f"
        result = IPCSanitizer.validate_binding(mock_binding)
        assert result is not None
        assert "Parameters" in result

    def test_invalid_description_returns_error(self, mock_binding):
        mock_binding.description = "Open\tterminal"
        result = IPCSanitizer.validate_binding(mock_binding)
        assert result is not None
        assert "Description" in result

    def test_invalid_modifier_returns_error(self, mock_binding):
        mock_binding.modifiers = ["SUPER", "SHIFT\x00"]
        result = IPCSanitizer.validate_binding(mock_binding)
        assert result is not None
        assert "Modifier" in result

    def test_none_params_is_valid(self, mock_binding):
        mock_binding.params = None
        result = IPCSanitizer.validate_binding(mock_binding)
        assert result is None

    def test_none_description_is_valid(self, mock_binding):
        mock_binding.description = None
        result = IPCSanitizer.validate_binding(mock_binding)
        assert result is None

    def test_empty_modifiers_is_valid(self, mock_binding):
        mock_binding.modifiers = []
        result = IPCSanitizer.validate_binding(mock_binding)
        assert result is None

    def test_returns_first_error_only(self, mock_binding):
        """Should return the first error found, not all errors."""
        mock_binding.key = "bad\x00key"
        mock_binding.action = "bad\naction"
        result = IPCSanitizer.validate_binding(mock_binding)
        # Should return Key error first (checked before Action)
        assert "Key" in result
