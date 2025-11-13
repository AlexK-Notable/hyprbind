"""GitHub profile fetcher for importing Hyprland configurations."""

import json
import base64
import re
import urllib.request
import urllib.error
from typing import Dict, List, Any

from hyprbind.core.config_manager import ConfigManager, OperationResult
from hyprbind.parsers.config_parser import ConfigParser


class GitHubFetcher:
    """Fetch and import Hyprland configurations from GitHub repositories."""

    # GitHub API base URL
    API_BASE = "https://api.github.com"

    # Common Hyprland config paths to search for
    CONFIG_PATHS = [
        ".config/hypr/hyprland.conf",
        ".config/hypr/config/keybinds.conf",
        "hypr/hyprland.conf",
        "hypr/config/keybinds.conf",
        "hypr/keybinds.conf",
        ".config/hypr/keybinds.conf",
    ]

    @staticmethod
    def validate_username(username: str) -> bool:
        """
        Validate GitHub username.

        Args:
            username: GitHub username to validate

        Returns:
            True if username is valid format
        """
        if not username:
            return False

        # GitHub usernames: alphanumeric and hyphens, no spaces or special chars
        pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$"
        return bool(re.match(pattern, username))

    @staticmethod
    def _make_request(url: str) -> Dict[str, Any]:
        """
        Make HTTP request to GitHub API.

        Args:
            url: URL to request

        Returns:
            Dictionary with success flag and data/error message
        """
        try:
            # Add User-Agent header (required by GitHub API)
            req = urllib.request.Request(
                url, headers={"User-Agent": "HyprBind-Config-Importer"}
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                return {"success": True, "data": data}

        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {"success": False, "message": "Resource not found"}
            elif e.code == 403:
                return {
                    "success": False,
                    "message": "API rate limit exceeded. Please try again later.",
                }
            else:
                return {
                    "success": False,
                    "message": f"HTTP error {e.code}: {e.reason}",
                }

        except urllib.error.URLError as e:
            return {"success": False, "message": f"Network error: {e.reason}"}

        except json.JSONDecodeError as e:
            return {"success": False, "message": f"Invalid JSON response: {e}"}

        except Exception as e:
            return {"success": False, "message": f"Unexpected error: {e}"}

    @staticmethod
    def fetch_profile(username: str) -> Dict[str, Any]:
        """
        Fetch GitHub profile and repositories.

        Args:
            username: GitHub username

        Returns:
            Dictionary with success flag and repository list or error message
        """
        if not GitHubFetcher.validate_username(username):
            return {"success": False, "message": "Invalid username format"}

        url = f"{GitHubFetcher.API_BASE}/users/{username}/repos"
        result = GitHubFetcher._make_request(url)

        if not result["success"]:
            return result

        # Parse repository data
        repos = []
        for repo in result["data"]:
            repos.append(
                {
                    "name": repo["name"],
                    "description": repo.get("description", ""),
                    "stars": repo.get("stargazers_count", 0),
                    "url": repo.get("html_url", ""),
                }
            )

        return {"success": True, "repos": repos, "username": username}

    @staticmethod
    def find_config_files(username: str, repo: str) -> Dict[str, Any]:
        """
        Find Hyprland config files in a repository.

        Args:
            username: GitHub username
            repo: Repository name

        Returns:
            Dictionary with success flag and list of config file paths
        """
        # Get repository tree (recursive)
        url = f"{GitHubFetcher.API_BASE}/repos/{username}/{repo}/git/trees/main?recursive=1"
        result = GitHubFetcher._make_request(url)

        if not result["success"]:
            # Try 'master' branch if 'main' doesn't exist
            url = f"{GitHubFetcher.API_BASE}/repos/{username}/{repo}/git/trees/master?recursive=1"
            result = GitHubFetcher._make_request(url)

            if not result["success"]:
                return result

        # Extract file paths from tree
        tree = result["data"].get("tree", [])
        all_files = [item["path"] for item in tree if item["type"] == "blob"]

        # Find Hyprland config files
        config_files = []
        for path in all_files:
            # Check if path matches any known config patterns
            if any(
                path.endswith(pattern) or path == pattern
                for pattern in GitHubFetcher.CONFIG_PATHS
            ):
                config_files.append(path)

            # Also check for any .conf files in hypr directories
            if "hypr" in path.lower() and path.endswith(".conf"):
                if path not in config_files:
                    config_files.append(path)

        message = (
            f"Found {len(config_files)} config file(s)"
            if config_files
            else "No config files found in repository"
        )

        return {"success": True, "files": config_files, "message": message}

    @staticmethod
    def download_config(username: str, repo: str, path: str) -> Dict[str, Any]:
        """
        Download config file content from repository.

        Args:
            username: GitHub username
            repo: Repository name
            path: Path to config file in repository

        Returns:
            Dictionary with success flag and file content or error message
        """
        url = f"{GitHubFetcher.API_BASE}/repos/{username}/{repo}/contents/{path}"
        result = GitHubFetcher._make_request(url)

        if not result["success"]:
            return result

        # Decode base64 content
        try:
            content_data = result["data"]
            if content_data.get("encoding") == "base64":
                content = base64.b64decode(content_data["content"]).decode("utf-8")
            else:
                content = content_data.get("content", "")

            return {"success": True, "content": content, "path": path}

        except Exception as e:
            return {"success": False, "message": f"Failed to decode content: {e}"}

    @staticmethod
    def import_to_config(
        config_content: str, config_manager: ConfigManager
    ) -> OperationResult:
        """
        Import config content into ConfigManager.

        Args:
            config_content: Raw config file content
            config_manager: ConfigManager instance to import into

        Returns:
            OperationResult with success status and message
        """
        if not config_content or not config_content.strip():
            return OperationResult(success=False, message="Config content is empty")

        if config_manager.config is None:
            return OperationResult(
                success=False, message="Config not loaded in ConfigManager"
            )

        try:
            # Parse the config content
            parsed_config = ConfigParser.parse_string(config_content)

            # Get all bindings from parsed config
            imported_bindings = parsed_config.get_all_bindings()

            if not imported_bindings:
                return OperationResult(
                    success=True,
                    message="Config parsed successfully but no bindings found",
                )

            # Add each binding to the config manager
            conflicts = []
            added_count = 0

            for binding in imported_bindings:
                result = config_manager.add_binding(binding)
                if result.success:
                    added_count += 1
                else:
                    # Track conflicts but continue importing
                    conflicts.extend(result.conflicts)

            # Create summary message
            if added_count == len(imported_bindings):
                message = f"Successfully imported {added_count} binding(s)"
            elif added_count > 0:
                message = (
                    f"Imported {added_count} binding(s), "
                    f"{len(imported_bindings) - added_count} skipped due to conflicts"
                )
            else:
                message = "No bindings imported - all conflicted with existing bindings"

            return OperationResult(
                success=added_count > 0, message=message, conflicts=conflicts
            )

        except Exception as e:
            return OperationResult(
                success=False, message=f"Failed to parse config: {e}"
            )
