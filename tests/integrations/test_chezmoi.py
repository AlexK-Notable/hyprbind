"""Tests for Chezmoi integration."""

import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import subprocess

from hyprbind.integrations.chezmoi import ChezmoiIntegration


class TestChezmoiIntegration(unittest.TestCase):
    """Test cases for Chezmoi integration functionality."""

    def test_is_installed_returns_true_when_chezmoi_exists(self):
        """Test that is_installed returns True when chezmoi is in PATH."""
        with patch('shutil.which', return_value='/usr/bin/chezmoi'):
            self.assertTrue(ChezmoiIntegration.is_installed())

    def test_is_installed_returns_false_when_chezmoi_missing(self):
        """Test that is_installed returns False when chezmoi is not in PATH."""
        with patch('shutil.which', return_value=None):
            self.assertFalse(ChezmoiIntegration.is_installed())

    def test_is_managed_returns_true_for_managed_file(self):
        """Test that is_managed returns True for a file managed by chezmoi."""
        test_file = Path('/home/user/.config/hypr/config/keybinds.conf')

        # Mock successful chezmoi source-path command
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '/home/user/.local/share/chezmoi/dot_config/hypr/config/keybinds.conf'

        with patch('subprocess.run', return_value=mock_result):
            self.assertTrue(ChezmoiIntegration.is_managed(test_file))

    def test_is_managed_returns_false_for_unmanaged_file(self):
        """Test that is_managed returns False for a file not managed by chezmoi."""
        test_file = Path('/home/user/.config/some/random/file.txt')

        # Mock failed chezmoi source-path command
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ''

        with patch('subprocess.run', return_value=mock_result):
            self.assertFalse(ChezmoiIntegration.is_managed(test_file))

    def test_is_managed_returns_false_when_chezmoi_not_installed(self):
        """Test that is_managed returns False when chezmoi is not installed."""
        test_file = Path('/home/user/.config/hypr/config/keybinds.conf')

        with patch('shutil.which', return_value=None):
            self.assertFalse(ChezmoiIntegration.is_managed(test_file))

    def test_is_managed_handles_subprocess_exception(self):
        """Test that is_managed handles subprocess exceptions gracefully."""
        test_file = Path('/home/user/.config/hypr/config/keybinds.conf')

        with patch('shutil.which', return_value='/usr/bin/chezmoi'):
            with patch('subprocess.run', side_effect=subprocess.SubprocessError('Command failed')):
                self.assertFalse(ChezmoiIntegration.is_managed(test_file))

    def test_get_source_path_returns_path_for_managed_file(self):
        """Test that get_source_path returns the source path for a managed file."""
        test_file = Path('/home/user/.config/hypr/config/keybinds.conf')
        expected_source = Path('/home/user/.local/share/chezmoi/dot_config/hypr/config/keybinds.conf')

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = str(expected_source) + '\n'  # chezmoi adds newline

        with patch('subprocess.run', return_value=mock_result):
            result = ChezmoiIntegration.get_source_path(test_file)
            self.assertEqual(result, expected_source)

    def test_get_source_path_returns_none_for_unmanaged_file(self):
        """Test that get_source_path returns None for an unmanaged file."""
        test_file = Path('/home/user/.config/some/file.txt')

        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ''

        with patch('subprocess.run', return_value=mock_result):
            result = ChezmoiIntegration.get_source_path(test_file)
            self.assertIsNone(result)

    def test_get_source_path_returns_none_when_chezmoi_not_installed(self):
        """Test that get_source_path returns None when chezmoi is not installed."""
        test_file = Path('/home/user/.config/hypr/config/keybinds.conf')

        with patch('shutil.which', return_value=None):
            result = ChezmoiIntegration.get_source_path(test_file)
            self.assertIsNone(result)

    def test_get_source_path_handles_subprocess_exception(self):
        """Test that get_source_path handles subprocess exceptions gracefully."""
        test_file = Path('/home/user/.config/hypr/config/keybinds.conf')

        with patch('shutil.which', return_value='/usr/bin/chezmoi'):
            with patch('subprocess.run', side_effect=subprocess.SubprocessError('Command failed')):
                result = ChezmoiIntegration.get_source_path(test_file)
                self.assertIsNone(result)

    def test_subprocess_called_with_correct_arguments(self):
        """Test that subprocess.run is called with correct chezmoi arguments."""
        test_file = Path('/home/user/.config/hypr/config/keybinds.conf')

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '/home/user/.local/share/chezmoi/dot_config/hypr/config/keybinds.conf'

        with patch('subprocess.run', return_value=mock_result) as mock_run:
            ChezmoiIntegration.is_managed(test_file)

            # Verify subprocess.run was called with correct arguments
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            self.assertEqual(call_args[0], 'chezmoi')
            self.assertEqual(call_args[1], 'source-path')
            self.assertEqual(call_args[2], str(test_file))

    def test_subprocess_called_with_correct_options(self):
        """Test that subprocess.run is called with correct options."""
        test_file = Path('/home/user/.config/hypr/config/keybinds.conf')

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '/home/user/.local/share/chezmoi/dot_config/hypr/config/keybinds.conf'

        with patch('subprocess.run', return_value=mock_result) as mock_run:
            ChezmoiIntegration.get_source_path(test_file)

            # Verify subprocess.run was called with correct options
            call_kwargs = mock_run.call_args[1]
            self.assertTrue(call_kwargs['capture_output'])
            self.assertEqual(call_kwargs['text'], True)
            self.assertIn('check', call_kwargs)
            self.assertFalse(call_kwargs['check'])

    def test_get_edit_command_returns_correct_command(self):
        """Test that get_edit_command returns the correct chezmoi edit command."""
        test_file = Path('/home/user/.config/hypr/config/keybinds.conf')
        expected_command = ['chezmoi', 'edit', str(test_file)]

        result = ChezmoiIntegration.get_edit_command(test_file)
        self.assertEqual(result, expected_command)

    def test_get_apply_command_returns_correct_command(self):
        """Test that get_apply_command returns the correct chezmoi apply command."""
        test_file = Path('/home/user/.config/hypr/config/keybinds.conf')
        expected_command = ['chezmoi', 'apply', str(test_file)]

        result = ChezmoiIntegration.get_apply_command(test_file)
        self.assertEqual(result, expected_command)

    def test_get_apply_all_command_returns_correct_command(self):
        """Test that get_apply_all_command returns the correct chezmoi apply command."""
        expected_command = ['chezmoi', 'apply']

        result = ChezmoiIntegration.get_apply_all_command()
        self.assertEqual(result, expected_command)


if __name__ == '__main__':
    unittest.main()
