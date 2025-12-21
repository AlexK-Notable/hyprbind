"""Path and input validation for security.

This module provides validators to prevent path traversal attacks and
restrict file operations to expected directories. It also validates
Hyprland actions for safety warnings.

Security Considerations:
    - GitHub paths: Prevent traversal in fetched content
    - Local paths: Restrict to hypr config directories
    - Symlinks: Validate final resolved paths
    - Actions: Warn about dangerous exec commands
"""

__all__ = ["PathValidator", "ActionValidator"]

import os
import re
from pathlib import Path
from typing import Optional, List

from .logging_config import get_logger

logger = get_logger(__name__)

# Pattern matching directory traversal attempts
PATH_TRAVERSAL = re.compile(r'(^|[/\\])\.\.[/\\]|^\.\./?$')


class PathValidator:
    """Validate file paths for security.

    This class provides methods to validate both remote paths (from GitHub)
    and local paths (on the filesystem) to prevent path traversal and
    unauthorized file access.
    """

    # Cached list of allowed directories (populated on first use)
    _allowed_dirs: Optional[List[Path]] = None

    @classmethod
    def _get_allowed_dirs(cls) -> List[Path]:
        """Get list of allowed config directories.

        Directories are determined from:
        1. XDG_CONFIG_HOME/hypr (if XDG_CONFIG_HOME is set)
        2. ~/.config/hypr (default)
        3. HYPRBIND_CONFIG_DIRS environment variable (escape hatch)

        Returns:
            List of allowed Path objects
        """
        if cls._allowed_dirs is not None:
            return cls._allowed_dirs

        dirs: List[Path] = []

        # XDG config directory
        xdg_config = os.environ.get('XDG_CONFIG_HOME', '')
        if xdg_config:
            dirs.append(Path(xdg_config) / 'hypr')

        # Default ~/.config/hypr
        dirs.append(Path.home() / '.config' / 'hypr')

        # Escape hatch for non-standard setups
        # Set HYPRBIND_CONFIG_DIRS=/path1:/path2 to allow additional directories
        custom = os.environ.get('HYPRBIND_CONFIG_DIRS', '')
        if custom:
            for d in custom.split(':'):
                if d.strip():
                    dirs.append(Path(d.strip()))

        cls._allowed_dirs = dirs
        logger.debug("Allowed config directories: %s", dirs)
        return dirs

    @classmethod
    def reset_allowed_dirs(cls) -> None:
        """Reset cached allowed directories (for testing)."""
        cls._allowed_dirs = None

    @classmethod
    def validate_github_path(cls, path: str) -> Optional[str]:
        """Validate a path from GitHub API response.

        Checks that the path:
        - Is not empty
        - Does not contain directory traversal (../)
        - Is not an absolute path
        - Matches expected Hyprland config patterns

        Args:
            path: Relative path from repository

        Returns:
            Error message if invalid, None if valid
        """
        if not path:
            return "Path cannot be empty"

        if PATH_TRAVERSAL.search(path):
            logger.warning("Path traversal attempt detected: %s", path)
            return "Path contains directory traversal"

        if path.startswith('/'):
            return "Absolute paths not allowed"

        # Allowlist of expected Hyprland config patterns
        allowed_patterns = [
            r'^\.?config/hypr/.*\.conf$',
            r'^hypr/.*\.conf$',
            r'^\.hypr/.*\.conf$',
            r'^[^/]*keybinds?\.conf$',
            r'^[^/]*binds?\.conf$',
            r'^[^/]*hyprland\.conf$',
        ]

        if not any(re.match(p, path, re.IGNORECASE) for p in allowed_patterns):
            return f"Path '{path}' doesn't match expected Hyprland config patterns"

        return None

    @classmethod
    def validate_local_path(
        cls,
        path: Path,
        must_exist: bool = True,
        allowed_dirs: Optional[List[Path]] = None
    ) -> Optional[str]:
        """Validate a local file path is within allowed directories.

        This method checks that the resolved path stays within the allowed
        config directories, following symlinks to prevent escape.

        Args:
            path: Path to validate
            must_exist: Whether the path must already exist (default True)
            allowed_dirs: Override default allowed directories

        Returns:
            Error message if invalid, None if valid
        """
        if allowed_dirs is None:
            allowed_dirs = cls._get_allowed_dirs()

        try:
            # Resolve to absolute path, following symlinks
            resolved = path.resolve()

            # Check existence if required
            if must_exist and not resolved.exists():
                return f"Path does not exist: {path}"

            # Check if within any allowed directory
            for allowed in allowed_dirs:
                try:
                    allowed_resolved = allowed.resolve()
                    # relative_to raises ValueError if not a subpath
                    resolved.relative_to(allowed_resolved)
                    return None  # Valid - within allowed directory
                except ValueError:
                    continue

            allowed_str = ', '.join(str(d) for d in allowed_dirs)
            return f"Path {path} is outside allowed config directories: {allowed_str}"

        except (OSError, RuntimeError) as e:
            logger.error("Path validation error for %s: %s", path, e)
            return f"Path validation error: {e}"

    @classmethod
    def validate_write_path(cls, path: Path) -> Optional[str]:
        """Validate a path is safe to write to.

        Additional checks beyond validate_local_path:
        - Parent directory must exist
        - Parent directory must be writable

        Args:
            path: Path to validate for writing

        Returns:
            Error message if invalid, None if valid
        """
        # First check it's in allowed directories (don't require existence)
        error = cls.validate_local_path(path, must_exist=False)
        if error:
            return error

        # Check parent exists and is writable
        parent = path.resolve().parent
        if not parent.exists():
            return f"Parent directory does not exist: {parent}"

        if not os.access(parent, os.W_OK):
            return f"Cannot write to directory: {parent}"

        return None


class ActionValidator:
    """Validate Hyprland actions for safety warnings.

    Some Hyprland actions like 'exec' can run arbitrary shell commands.
    This validator provides warnings (not blocks) for potentially
    dangerous actions.
    """

    DANGEROUS_ACTIONS = frozenset({'exec', 'execr'})
    """Actions that execute shell commands."""

    @classmethod
    def check_dangerous_action(cls, action: str, params: str) -> Optional[str]:
        """Check if action could execute arbitrary commands.

        This returns a warning message for informational purposes.
        It does NOT block the action - users may legitimately want exec bindings.

        Args:
            action: The Hyprland action (e.g., 'exec', 'workspace')
            params: The action parameters

        Returns:
            Warning message if dangerous, None otherwise
        """
        if action.lower() in cls.DANGEROUS_ACTIONS:
            return (
                f"'{action}' executes shell commands. "
                f"Please verify: {params}"
            )
        return None
