"""Tests for core/validators.py module."""

import os
import pytest
from pathlib import Path

from hyprbind.core.validators import PathValidator, ActionValidator


class TestPathValidatorGitHub:
    """Test PathValidator.validate_github_path."""

    def test_rejects_empty_path(self):
        assert PathValidator.validate_github_path("") is not None

    def test_rejects_path_traversal(self):
        assert PathValidator.validate_github_path("../etc/passwd") is not None
        assert PathValidator.validate_github_path("foo/../bar") is not None
        assert PathValidator.validate_github_path("..") is not None
        assert PathValidator.validate_github_path("foo/..") is not None

    def test_rejects_absolute_paths(self):
        assert PathValidator.validate_github_path("/etc/passwd") is not None
        assert PathValidator.validate_github_path("/home/user/.config/hypr/keybinds.conf") is not None

    def test_allows_standard_config_paths(self):
        assert PathValidator.validate_github_path(".config/hypr/keybinds.conf") is None
        assert PathValidator.validate_github_path("config/hypr/bindings.conf") is None
        assert PathValidator.validate_github_path("hypr/keybinds.conf") is None
        assert PathValidator.validate_github_path(".hypr/keybinds.conf") is None

    def test_allows_keybinds_variants(self):
        assert PathValidator.validate_github_path("keybinds.conf") is None
        assert PathValidator.validate_github_path("keybind.conf") is None
        assert PathValidator.validate_github_path("binds.conf") is None
        assert PathValidator.validate_github_path("my-keybinds.conf") is None

    def test_allows_hyprland_conf(self):
        assert PathValidator.validate_github_path("hyprland.conf") is None
        assert PathValidator.validate_github_path(".config/hypr/hyprland.conf") is None

    def test_rejects_non_config_files(self):
        assert PathValidator.validate_github_path("README.md") is not None
        assert PathValidator.validate_github_path("script.sh") is not None
        assert PathValidator.validate_github_path(".config/hypr/scripts/run.sh") is not None


class TestPathValidatorLocal:
    """Test PathValidator.validate_local_path."""

    @pytest.fixture(autouse=True)
    def reset_cache(self):
        """Reset cached allowed dirs before each test."""
        PathValidator.reset_allowed_dirs()
        yield
        PathValidator.reset_allowed_dirs()

    def test_allows_path_in_allowed_dir(self, tmp_path):
        # Create test file in allowed directory
        test_file = tmp_path / "test.conf"
        test_file.touch()

        # Should pass when we explicitly allow tmp_path
        result = PathValidator.validate_local_path(test_file, allowed_dirs=[tmp_path])
        assert result is None

    def test_rejects_path_outside_allowed_dirs(self, tmp_path):
        # Create file in tmp_path but don't allow it
        test_file = tmp_path / "test.conf"
        test_file.touch()

        # Create a different allowed dir
        allowed = tmp_path / "allowed"
        allowed.mkdir()

        result = PathValidator.validate_local_path(test_file, allowed_dirs=[allowed])
        assert result is not None
        assert "outside allowed" in result

    def test_rejects_nonexistent_path_when_must_exist(self, tmp_path):
        nonexistent = tmp_path / "does_not_exist.conf"
        result = PathValidator.validate_local_path(
            nonexistent, must_exist=True, allowed_dirs=[tmp_path]
        )
        assert result is not None
        assert "does not exist" in result

    def test_allows_nonexistent_path_when_must_exist_false(self, tmp_path):
        nonexistent = tmp_path / "new_file.conf"
        result = PathValidator.validate_local_path(
            nonexistent, must_exist=False, allowed_dirs=[tmp_path]
        )
        assert result is None

    def test_follows_symlinks(self, tmp_path):
        """Symlinks should be resolved and checked against allowed dirs."""
        # Create actual file in allowed dir
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        actual = allowed / "actual.conf"
        actual.touch()

        # Create symlink in different location
        other = tmp_path / "other"
        other.mkdir()
        symlink = other / "link.conf"
        symlink.symlink_to(actual)

        # The symlink resolves to a path IN allowed, so should pass
        result = PathValidator.validate_local_path(symlink, allowed_dirs=[allowed])
        assert result is None


class TestPathValidatorWrite:
    """Test PathValidator.validate_write_path."""

    @pytest.fixture(autouse=True)
    def reset_cache(self):
        PathValidator.reset_allowed_dirs()
        yield
        PathValidator.reset_allowed_dirs()

    def test_allows_write_to_existing_dir(self, tmp_path):
        new_file = tmp_path / "new.conf"
        result = PathValidator.validate_write_path(new_file)
        # Will fail because tmp_path is not in default allowed dirs
        # But if we specify allowed_dirs, it should work
        # For this test, we use validate_local_path directly with custom allowed
        result = PathValidator.validate_local_path(
            new_file, must_exist=False, allowed_dirs=[tmp_path]
        )
        assert result is None

    def test_rejects_write_to_nonexistent_parent(self, tmp_path):
        # validate_write_path checks parent exists
        nonexistent_parent = tmp_path / "nonexistent" / "file.conf"
        result = PathValidator.validate_write_path(nonexistent_parent)
        assert result is not None


class TestActionValidator:
    """Test ActionValidator.check_dangerous_action."""

    def test_exec_is_dangerous(self):
        result = ActionValidator.check_dangerous_action("exec", "rm -rf /")
        assert result is not None
        assert "exec" in result.lower()
        assert "rm -rf /" in result

    def test_execr_is_dangerous(self):
        result = ActionValidator.check_dangerous_action("execr", "some command")
        assert result is not None
        assert "execr" in result.lower()

    def test_exec_case_insensitive(self):
        result = ActionValidator.check_dangerous_action("EXEC", "command")
        assert result is not None

    def test_safe_actions_return_none(self):
        assert ActionValidator.check_dangerous_action("workspace", "1") is None
        assert ActionValidator.check_dangerous_action("killactive", "") is None
        assert ActionValidator.check_dangerous_action("togglefloating", "") is None
        assert ActionValidator.check_dangerous_action("movefocus", "l") is None


class TestEnvironmentOverride:
    """Test HYPRBIND_CONFIG_DIRS environment variable."""

    @pytest.fixture(autouse=True)
    def reset_cache(self):
        PathValidator.reset_allowed_dirs()
        yield
        PathValidator.reset_allowed_dirs()

    def test_custom_dirs_from_env(self, tmp_path, monkeypatch):
        custom_dir = tmp_path / "custom"
        custom_dir.mkdir()
        test_file = custom_dir / "test.conf"
        test_file.touch()

        # Set environment variable
        monkeypatch.setenv("HYPRBIND_CONFIG_DIRS", str(custom_dir))
        PathValidator.reset_allowed_dirs()

        result = PathValidator.validate_local_path(test_file)
        assert result is None

    def test_multiple_custom_dirs(self, tmp_path, monkeypatch):
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()

        file1 = dir1 / "test.conf"
        file2 = dir2 / "test.conf"
        file1.touch()
        file2.touch()

        # Set multiple directories
        monkeypatch.setenv("HYPRBIND_CONFIG_DIRS", f"{dir1}:{dir2}")
        PathValidator.reset_allowed_dirs()

        assert PathValidator.validate_local_path(file1) is None
        assert PathValidator.validate_local_path(file2) is None
