"""Tests for GitHub profile fetcher."""

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json

from hyprbind.integrations.github_fetcher import GitHubFetcher
from hyprbind.core.config_manager import ConfigManager, OperationResult
from hyprbind.core.models import Config, Binding, BindType


class TestGitHubFetcher(unittest.TestCase):
    """Test GitHub profile fetching functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.username = "testuser"
        self.repo = "hyprland-config"

        # Sample GitHub API responses
        self.repos_response = [
            {
                "name": "hyprland-config",
                "description": "My Hyprland configuration",
                "stargazers_count": 100,
                "html_url": "https://github.com/testuser/hyprland-config",
            },
            {
                "name": "other-repo",
                "description": "Other stuff",
                "stargazers_count": 50,
                "html_url": "https://github.com/testuser/other-repo",
            },
        ]

        self.tree_response = {
            "tree": [
                {"path": ".config", "type": "tree"},
                {"path": ".config/hypr", "type": "tree"},
                {"path": ".config/hypr/hyprland.conf", "type": "blob"},
                {"path": ".config/hypr/config", "type": "tree"},
                {"path": ".config/hypr/config/keybinds.conf", "type": "blob"},
                {"path": "README.md", "type": "blob"},
            ]
        }

        self.keybinds_content = """# ======= Window Management =======
bindd = $mainMod, Q, Close window, killactive
bindd = $mainMod, F, Toggle fullscreen, fullscreen

# ======= Applications =======
bindd = $mainMod, RETURN, Open terminal, exec, alacritty
bindd = $mainMod, SPACE, App launcher, exec, walker
"""

        self.file_response = {
            "content": self._base64_encode(self.keybinds_content),
            "encoding": "base64",
        }

    def _base64_encode(self, text: str) -> str:
        """Encode text to base64."""
        import base64

        return base64.b64encode(text.encode()).decode()

    @patch("urllib.request.urlopen")
    def test_fetch_profile_success(self, mock_urlopen):
        """Test successful profile fetching."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(self.repos_response).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        result = GitHubFetcher.fetch_profile(self.username)

        self.assertTrue(result["success"])
        self.assertEqual(len(result["repos"]), 2)
        self.assertEqual(result["repos"][0]["name"], "hyprland-config")
        mock_urlopen.assert_called_once()

    @patch("urllib.request.urlopen")
    def test_fetch_profile_user_not_found(self, mock_urlopen):
        """Test profile fetching with non-existent user."""
        # Mock 404 response
        from urllib.error import HTTPError

        mock_urlopen.side_effect = HTTPError(
            url="test", code=404, msg="Not Found", hdrs={}, fp=None
        )

        result = GitHubFetcher.fetch_profile("nonexistentuser")

        self.assertFalse(result["success"])
        self.assertIn("not found", result["message"].lower())

    @patch("urllib.request.urlopen")
    def test_fetch_profile_network_error(self, mock_urlopen):
        """Test profile fetching with network error."""
        from urllib.error import URLError

        mock_urlopen.side_effect = URLError("Network error")

        result = GitHubFetcher.fetch_profile(self.username)

        self.assertFalse(result["success"])
        self.assertIn("network", result["message"].lower())

    @patch("urllib.request.urlopen")
    def test_find_config_files_success(self, mock_urlopen):
        """Test finding config files in repository."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(self.tree_response).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        result = GitHubFetcher.find_config_files(self.username, self.repo)

        self.assertTrue(result["success"])
        self.assertIn(".config/hypr/config/keybinds.conf", result["files"])
        self.assertIn(".config/hypr/hyprland.conf", result["files"])

    @patch("urllib.request.urlopen")
    def test_find_config_files_no_configs(self, mock_urlopen):
        """Test finding config files when none exist."""
        # Mock empty tree response
        empty_tree = {"tree": [{"path": "README.md", "type": "blob"}]}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(empty_tree).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        result = GitHubFetcher.find_config_files(self.username, self.repo)

        self.assertTrue(result["success"])
        self.assertEqual(len(result["files"]), 0)
        self.assertIn("no config files", result["message"].lower())

    @patch("urllib.request.urlopen")
    def test_download_config_success(self, mock_urlopen):
        """Test successful config download."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(self.file_response).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        result = GitHubFetcher.download_config(
            self.username, self.repo, ".config/hypr/config/keybinds.conf"
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["content"], self.keybinds_content)
        self.assertIn("Window Management", result["content"])

    @patch("urllib.request.urlopen")
    def test_download_config_file_not_found(self, mock_urlopen):
        """Test downloading non-existent config file."""
        from urllib.error import HTTPError

        mock_urlopen.side_effect = HTTPError(
            url="test", code=404, msg="Not Found", hdrs={}, fp=None
        )

        result = GitHubFetcher.download_config(
            self.username, self.repo, "nonexistent.conf"
        )

        self.assertFalse(result["success"])
        self.assertIn("not found", result["message"].lower())

    @patch("urllib.request.urlopen")
    def test_import_to_config_success(self, mock_urlopen):
        """Test importing config content to ConfigManager."""
        # Create a test config manager with empty config
        config_manager = ConfigManager()
        config_manager.config = Config()

        result = GitHubFetcher.import_to_config(
            self.keybinds_content, config_manager
        )

        self.assertTrue(result.success)
        # Check that bindings were added
        all_bindings = config_manager.config.get_all_bindings()
        self.assertEqual(len(all_bindings), 4)  # 4 bindings in test content
        # Check categories were created
        self.assertIn("Window Management", config_manager.config.categories)
        self.assertIn("Applications", config_manager.config.categories)

    def test_import_to_config_empty_content(self):
        """Test importing empty config content."""
        config_manager = ConfigManager()
        config_manager.config = Config()

        result = GitHubFetcher.import_to_config("", config_manager)

        self.assertFalse(result.success)
        self.assertIn("empty", result.message.lower())

    def test_import_to_config_parse_error(self):
        """Test importing malformed config content."""
        config_manager = ConfigManager()
        config_manager.config = Config()

        # This should parse but result in no bindings
        malformed_content = "not a valid config\nrandom text\n"

        result = GitHubFetcher.import_to_config(malformed_content, config_manager)

        # Should succeed but with warning about no bindings
        self.assertTrue(result.success)
        self.assertIn("no bindings", result.message.lower())

    @patch("urllib.request.urlopen")
    def test_fetch_complete_workflow(self, mock_urlopen):
        """Test complete workflow from profile to import."""
        # Mock sequence of API calls
        responses = [
            # 1. fetch_profile - repos list
            json.dumps(self.repos_response).encode(),
            # 2. find_config_files - tree
            json.dumps(self.tree_response).encode(),
            # 3. download_config - file content
            json.dumps(self.file_response).encode(),
        ]

        mock_response = MagicMock()
        mock_response.read.side_effect = responses
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        # Step 1: Fetch profile
        profile_result = GitHubFetcher.fetch_profile(self.username)
        self.assertTrue(profile_result["success"])

        # Step 2: Find config files
        files_result = GitHubFetcher.find_config_files(self.username, self.repo)
        self.assertTrue(files_result["success"])
        self.assertGreater(len(files_result["files"]), 0)

        # Step 3: Download config
        download_result = GitHubFetcher.download_config(
            self.username, self.repo, files_result["files"][0]
        )
        self.assertTrue(download_result["success"])

        # Step 4: Import to config
        config_manager = ConfigManager()
        config_manager.config = Config()
        import_result = GitHubFetcher.import_to_config(
            download_result["content"], config_manager
        )
        self.assertTrue(import_result.success)

    @patch("urllib.request.urlopen")
    def test_rate_limit_handling(self, mock_urlopen):
        """Test handling of GitHub API rate limit."""
        from urllib.error import HTTPError

        # Mock 403 rate limit response
        mock_urlopen.side_effect = HTTPError(
            url="test", code=403, msg="Rate limit exceeded", hdrs={}, fp=None
        )

        result = GitHubFetcher.fetch_profile(self.username)

        self.assertFalse(result["success"])
        self.assertIn("rate limit", result["message"].lower())

    def test_validate_username(self):
        """Test username validation."""
        # Valid usernames
        self.assertTrue(GitHubFetcher.validate_username("user123"))
        self.assertTrue(GitHubFetcher.validate_username("user-name"))
        self.assertTrue(GitHubFetcher.validate_username("User"))

        # Invalid usernames
        self.assertFalse(GitHubFetcher.validate_username(""))
        self.assertFalse(GitHubFetcher.validate_username("user name"))
        self.assertFalse(GitHubFetcher.validate_username("user@name"))
        self.assertFalse(GitHubFetcher.validate_username("user/name"))


if __name__ == "__main__":
    unittest.main()
