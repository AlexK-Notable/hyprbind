"""Tests for core/constants.py module."""

import pytest

from hyprbind.core.constants import (
    BACKUP_KEEP_COUNT,
    IPC_TIMEOUT_SECONDS,
    GITHUB_REQUEST_TIMEOUT,
    VALID_MODIFIERS,
    VARIABLE_PATTERN,
    is_valid_modifier,
)


class TestConstants:
    """Test constant values are sensible."""

    def test_backup_keep_count_is_positive(self):
        assert BACKUP_KEEP_COUNT > 0

    def test_ipc_timeout_is_positive(self):
        assert IPC_TIMEOUT_SECONDS > 0

    def test_github_timeout_is_positive(self):
        assert GITHUB_REQUEST_TIMEOUT > 0

    def test_valid_modifiers_contains_common_mods(self):
        assert "SUPER" in VALID_MODIFIERS
        assert "SHIFT" in VALID_MODIFIERS
        assert "ALT" in VALID_MODIFIERS
        assert "CTRL" in VALID_MODIFIERS


class TestIsValidModifier:
    """Test is_valid_modifier function."""

    def test_builtin_modifiers_are_valid(self):
        assert is_valid_modifier("SUPER") is True
        assert is_valid_modifier("SHIFT") is True
        assert is_valid_modifier("ALT") is True
        assert is_valid_modifier("CTRL") is True

    def test_case_insensitive(self):
        assert is_valid_modifier("super") is True
        assert is_valid_modifier("Super") is True
        assert is_valid_modifier("SUPER") is True

    def test_variable_references_are_valid(self):
        assert is_valid_modifier("$mainMod") is True
        assert is_valid_modifier("$shiftMod") is True
        assert is_valid_modifier("$myCustomMod") is True

    def test_invalid_modifiers_rejected(self):
        assert is_valid_modifier("INVALID") is False
        assert is_valid_modifier("") is False
        assert is_valid_modifier("SUPERKEY") is False

    def test_partial_variable_not_valid(self):
        assert is_valid_modifier("$") is False
        assert is_valid_modifier("mainMod") is False  # Missing $


class TestVariablePattern:
    """Test VARIABLE_PATTERN regex."""

    def test_matches_valid_variables(self):
        assert VARIABLE_PATTERN.match("$mainMod")
        assert VARIABLE_PATTERN.match("$a")
        assert VARIABLE_PATTERN.match("$MOD1")
        assert VARIABLE_PATTERN.match("$_underscore")

    def test_rejects_invalid_variables(self):
        assert not VARIABLE_PATTERN.match("mainMod")  # No $
        assert not VARIABLE_PATTERN.match("$")  # Empty name
        assert not VARIABLE_PATTERN.match("$main-mod")  # Hyphen not allowed
        assert not VARIABLE_PATTERN.match("$$double")  # Double $
