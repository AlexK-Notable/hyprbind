"""Chezmoi integration for detecting and managing dotfiles."""

import shutil
import subprocess
from pathlib import Path
from typing import Optional


class ChezmoiIntegration:
    """Integration with Chezmoi dotfile manager."""

    @staticmethod
    def is_installed() -> bool:
        """
        Check if Chezmoi is installed on the system.

        Returns:
            bool: True if chezmoi is in PATH, False otherwise.
        """
        return shutil.which('chezmoi') is not None

    @staticmethod
    def is_managed(file_path: Path) -> bool:
        """
        Check if a file is managed by Chezmoi.

        Args:
            file_path: Path to the file to check.

        Returns:
            bool: True if the file is managed by Chezmoi, False otherwise.
        """
        if not ChezmoiIntegration.is_installed():
            return False

        try:
            result = subprocess.run(
                ['chezmoi', 'source-path', str(file_path)],
                capture_output=True,
                text=True,
                check=False,
            )
            return result.returncode == 0
        except subprocess.SubprocessError:
            return False

    @staticmethod
    def get_source_path(file_path: Path) -> Optional[Path]:
        """
        Get the Chezmoi source path for a managed file.

        Args:
            file_path: Path to the file to check.

        Returns:
            Path: Path to the source file in Chezmoi's source directory,
                  or None if the file is not managed by Chezmoi.
        """
        if not ChezmoiIntegration.is_installed():
            return None

        try:
            result = subprocess.run(
                ['chezmoi', 'source-path', str(file_path)],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0 and result.stdout.strip():
                return Path(result.stdout.strip())

            return None
        except subprocess.SubprocessError:
            return None

    @staticmethod
    def get_edit_command(file_path: Path) -> list[str]:
        """
        Get the command to edit a file via Chezmoi.

        Args:
            file_path: Path to the file to edit.

        Returns:
            list[str]: Command to edit the file with Chezmoi.
        """
        return ['chezmoi', 'edit', str(file_path)]

    @staticmethod
    def get_apply_command(file_path: Path) -> list[str]:
        """
        Get the command to apply changes to a specific file.

        Args:
            file_path: Path to the file to apply.

        Returns:
            list[str]: Command to apply the file with Chezmoi.
        """
        return ['chezmoi', 'apply', str(file_path)]

    @staticmethod
    def get_apply_all_command() -> list[str]:
        """
        Get the command to apply all Chezmoi changes.

        Returns:
            list[str]: Command to apply all changes with Chezmoi.
        """
        return ['chezmoi', 'apply']
