# Performance Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix two critical performance bottlenecks: O(n²) conflict detection and blocking network operations.

**Architecture:**
1. Add hash-based binding index to Config model for O(1) conflict lookups
2. Convert synchronous network fetches to async with GLib integration for responsive UI

**Tech Stack:** Python 3.11+, GTK4, GLib, threading

---

## Part 1: Hash-Based O(1) Conflict Detection

### Problem Analysis

Current conflict detection in `ConflictDetector.check()` does a linear scan of all bindings (O(n)). When importing N bindings from GitHub, each triggers a conflict check, resulting in O(n²) total operations. For 100+ bindings, this causes noticeable freezes.

**Solution:** Add a hash index to `Config` that maps `(sorted_modifiers, key, submap)` tuples to bindings for O(1) lookups.

---

### Task 1: Add Conflict Key Generation to Binding Model

**Files:**
- Modify: `src/hyprbind/core/models.py:52-64`
- Test: `tests/core/test_models.py`

**Step 1: Write the failing test**

Add to `tests/core/test_models.py`:

```python
def test_binding_conflict_key():
    """Test conflict_key property generates consistent hash keys."""
    binding = Binding(
        type=BindType.BIND,
        modifiers=["SHIFT", "$mainMod"],  # Note: order varies
        key="Q",
        description="",
        action="killactive",
        params="",
        submap=None,
        line_number=1,
        category="Window",
    )

    # Key should be a tuple of (sorted modifiers tuple, key, submap)
    expected_key = (("$mainMod", "SHIFT"), "Q", None)
    assert binding.conflict_key == expected_key


def test_binding_conflict_key_different_modifier_order():
    """Test conflict_key is same regardless of modifier order."""
    binding1 = Binding(
        type=BindType.BIND,
        modifiers=["SHIFT", "$mainMod"],
        key="Q",
        description="",
        action="exec",
        params="",
        submap=None,
        line_number=1,
        category="Window",
    )

    binding2 = Binding(
        type=BindType.BIND,
        modifiers=["$mainMod", "SHIFT"],  # Different order
        key="Q",
        description="",
        action="killactive",
        params="",
        submap=None,
        line_number=2,
        category="Window",
    )

    assert binding1.conflict_key == binding2.conflict_key


def test_binding_conflict_key_with_submap():
    """Test conflict_key includes submap."""
    binding = Binding(
        type=BindType.BIND,
        modifiers=["$mainMod"],
        key="Q",
        description="",
        action="exec",
        params="",
        submap="resize",
        line_number=1,
        category="Window",
    )

    expected_key = (("$mainMod",), "Q", "resize")
    assert binding.conflict_key == expected_key
```

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=/home/komi/repos/hyprbind/worktrees/dev/src /home/komi/repos/hyprbind/worktrees/dev/.venv/bin/python -m pytest tests/core/test_models.py::test_binding_conflict_key -v`

Expected: FAIL with "AttributeError: 'Binding' object has no attribute 'conflict_key'"

**Step 3: Write minimal implementation**

Add to `src/hyprbind/core/models.py` in the `Binding` class, after line 64:

```python
    @property
    def conflict_key(self) -> tuple:
        """Generate hash key for conflict detection.

        Returns:
            Tuple of (sorted_modifiers, key, submap) for consistent hashing.
        """
        return (tuple(sorted(self.modifiers)), self.key, self.submap)
```

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=/home/komi/repos/hyprbind/worktrees/dev/src /home/komi/repos/hyprbind/worktrees/dev/.venv/bin/python -m pytest tests/core/test_models.py::test_binding_conflict_key tests/core/test_models.py::test_binding_conflict_key_different_modifier_order tests/core/test_models.py::test_binding_conflict_key_with_submap -v`

Expected: PASS

**Step 5: Commit**

```bash
cd /home/komi/repos/hyprbind/worktrees/dev && git add tests/core/test_models.py src/hyprbind/core/models.py && git commit -m "feat(models): add conflict_key property for O(1) conflict lookups"
```

---

### Task 2: Add Binding Index to Config Model

**Files:**
- Modify: `src/hyprbind/core/models.py:78-99`
- Test: `tests/core/test_models.py`

**Step 1: Write the failing test**

Add to `tests/core/test_models.py`:

```python
def test_config_binding_index_created():
    """Test binding index is maintained when adding bindings."""
    config = Config()
    binding = Binding(
        type=BindType.BIND,
        modifiers=["$mainMod"],
        key="Q",
        description="",
        action="killactive",
        params="",
        submap=None,
        line_number=1,
        category="Window",
    )

    config.add_binding(binding)

    # Index should contain the binding
    assert binding.conflict_key in config._binding_index
    assert config._binding_index[binding.conflict_key] == binding


def test_config_find_conflict_returns_binding():
    """Test find_conflict returns conflicting binding."""
    config = Config()
    existing = Binding(
        type=BindType.BIND,
        modifiers=["$mainMod"],
        key="Q",
        description="",
        action="killactive",
        params="",
        submap=None,
        line_number=1,
        category="Window",
    )

    config.add_binding(existing)

    new_binding = Binding(
        type=BindType.BIND,
        modifiers=["$mainMod"],
        key="Q",
        description="",
        action="exec",
        params="other",
        submap=None,
        line_number=2,
        category="Apps",
    )

    conflict = config.find_conflict(new_binding)
    assert conflict == existing


def test_config_find_conflict_returns_none_when_no_conflict():
    """Test find_conflict returns None when no conflict exists."""
    config = Config()
    existing = Binding(
        type=BindType.BIND,
        modifiers=["$mainMod"],
        key="Q",
        description="",
        action="killactive",
        params="",
        submap=None,
        line_number=1,
        category="Window",
    )

    config.add_binding(existing)

    new_binding = Binding(
        type=BindType.BIND,
        modifiers=["$mainMod"],
        key="W",  # Different key
        description="",
        action="exec",
        params="other",
        submap=None,
        line_number=2,
        category="Apps",
    )

    conflict = config.find_conflict(new_binding)
    assert conflict is None


def test_config_remove_binding_updates_index():
    """Test removing binding updates the index."""
    config = Config()
    binding = Binding(
        type=BindType.BIND,
        modifiers=["$mainMod"],
        key="Q",
        description="",
        action="killactive",
        params="",
        submap=None,
        line_number=1,
        category="Window",
    )

    config.add_binding(binding)
    assert binding.conflict_key in config._binding_index

    config.remove_binding(binding)
    assert binding.conflict_key not in config._binding_index
```

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=/home/komi/repos/hyprbind/worktrees/dev/src /home/komi/repos/hyprbind/worktrees/dev/.venv/bin/python -m pytest tests/core/test_models.py::test_config_binding_index_created -v`

Expected: FAIL with "AttributeError: 'Config' object has no attribute '_binding_index'"

**Step 3: Write minimal implementation**

Modify `src/hyprbind/core/models.py` Config class:

```python
@dataclass
class Config:
    """Complete Hyprland keybinding configuration."""

    categories: dict[str, Category] = field(default_factory=dict)
    variables: dict[str, str] = field(default_factory=dict)
    submaps: dict[str, List[Binding]] = field(default_factory=dict)
    file_path: Optional[str] = None
    original_content: str = ""
    _binding_index: dict[tuple, Binding] = field(default_factory=dict, repr=False)

    def add_binding(self, binding: Binding) -> None:
        """Add binding to appropriate category and update index."""
        if binding.category not in self.categories:
            self.categories[binding.category] = Category(name=binding.category)
        self.categories[binding.category].bindings.append(binding)
        # Update conflict detection index
        self._binding_index[binding.conflict_key] = binding

    def remove_binding(self, binding: Binding) -> None:
        """Remove binding from category and update index."""
        if binding.category in self.categories:
            category = self.categories[binding.category]
            if binding in category.bindings:
                category.bindings.remove(binding)
        # Update conflict detection index
        self._binding_index.pop(binding.conflict_key, None)

    def find_conflict(self, binding: Binding) -> Optional[Binding]:
        """Find conflicting binding in O(1) time.

        Args:
            binding: Binding to check for conflicts

        Returns:
            Conflicting binding if found, None otherwise
        """
        return self._binding_index.get(binding.conflict_key)

    def get_all_bindings(self) -> List[Binding]:
        """Get flat list of all bindings."""
        all_bindings = []
        for category in self.categories.values():
            all_bindings.extend(category.bindings)
        return all_bindings
```

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=/home/komi/repos/hyprbind/worktrees/dev/src /home/komi/repos/hyprbind/worktrees/dev/.venv/bin/python -m pytest tests/core/test_models.py::test_config_binding_index_created tests/core/test_models.py::test_config_find_conflict_returns_binding tests/core/test_models.py::test_config_find_conflict_returns_none_when_no_conflict tests/core/test_models.py::test_config_remove_binding_updates_index -v`

Expected: PASS

**Step 5: Commit**

```bash
cd /home/komi/repos/hyprbind/worktrees/dev && git add tests/core/test_models.py src/hyprbind/core/models.py && git commit -m "feat(models): add binding index for O(1) conflict detection"
```

---

### Task 3: Update ConflictDetector to Use Index

**Files:**
- Modify: `src/hyprbind/core/conflict_detector.py`
- Test: `tests/core/test_conflict_detector.py`

**Step 1: Write the failing test**

Add to `tests/core/test_conflict_detector.py`:

```python
def test_conflict_detector_uses_index():
    """Test ConflictDetector uses O(1) index lookup."""
    config = Config()

    # Add 100 bindings
    for i in range(100):
        binding = Binding(
            type=BindType.BIND,
            modifiers=["$mainMod"],
            key=f"F{i}",
            description="",
            action="exec",
            params=f"action{i}",
            submap=None,
            line_number=i,
            category="Test",
        )
        config.add_binding(binding)

    # Check for conflict with last binding
    new_binding = Binding(
        type=BindType.BIND,
        modifiers=["$mainMod"],
        key="F99",  # Conflicts with last one
        description="",
        action="exec",
        params="conflict",
        submap=None,
        line_number=101,
        category="Test",
    )

    # Should find conflict efficiently
    conflicts = ConflictDetector.check(new_binding, config)
    assert len(conflicts) == 1
    assert conflicts[0].key == "F99"
```

**Step 2: Run test to verify it passes (current implementation should work)**

Run: `PYTHONPATH=/home/komi/repos/hyprbind/worktrees/dev/src /home/komi/repos/hyprbind/worktrees/dev/.venv/bin/python -m pytest tests/core/test_conflict_detector.py::test_conflict_detector_uses_index -v`

Expected: PASS (functionality preserved)

**Step 3: Refactor ConflictDetector to use index**

Replace `src/hyprbind/core/conflict_detector.py`:

```python
"""Detect keybinding conflicts."""

from typing import List, Optional

from hyprbind.core.models import Binding, Config


class ConflictDetector:
    """Detect conflicts between keybindings."""

    @staticmethod
    def check(binding: Binding, config: Config) -> List[Binding]:
        """
        Check if binding conflicts with existing bindings.

        Uses O(1) hash index lookup for performance.

        Args:
            binding: New binding to check
            config: Current configuration

        Returns:
            List of conflicting bindings (empty if no conflicts)
        """
        conflict = config.find_conflict(binding)
        return [conflict] if conflict else []

    @staticmethod
    def has_conflicts(binding: Binding, config: Config) -> bool:
        """
        Quick check if binding has any conflicts.

        Args:
            binding: New binding to check
            config: Current configuration

        Returns:
            True if conflicts exist
        """
        return config.find_conflict(binding) is not None
```

**Step 4: Run all conflict detector tests**

Run: `PYTHONPATH=/home/komi/repos/hyprbind/worktrees/dev/src /home/komi/repos/hyprbind/worktrees/dev/.venv/bin/python -m pytest tests/core/test_conflict_detector.py -v`

Expected: PASS (all tests)

**Step 5: Commit**

```bash
cd /home/komi/repos/hyprbind/worktrees/dev && git add src/hyprbind/core/conflict_detector.py tests/core/test_conflict_detector.py && git commit -m "perf(conflict): use O(1) hash index instead of O(n) linear scan"
```

---

### Task 4: Update ConfigManager to Handle Index on Binding Updates

**Files:**
- Modify: `src/hyprbind/core/config_manager.py`
- Test: `tests/core/test_config_manager.py`

**Step 1: Check existing update_binding implementation**

Read the current `update_binding` method and ensure it properly removes old binding and adds new one (which will update index).

**Step 2: Run full test suite to ensure no regressions**

Run: `PYTHONPATH=/home/komi/repos/hyprbind/worktrees/dev/src /home/komi/repos/hyprbind/worktrees/dev/.venv/bin/python -m pytest tests/ -v --tb=short`

Expected: All tests PASS

**Step 3: Commit if changes needed**

```bash
cd /home/komi/repos/hyprbind/worktrees/dev && git add -A && git commit -m "fix(config_manager): ensure binding index updated on modifications"
```

---

## Part 2: Async Network Operations

### Problem Analysis

`GitHubFetcher._make_request()` uses synchronous `urllib.request.urlopen()` which blocks the GTK main thread. When importing from GitHub, the UI freezes for 5-10 seconds.

**Solution:** Create async wrapper using threading + `GLib.idle_add()` for callbacks on the main thread.

---

### Task 5: Create Async GitHubFetcher Methods

**Files:**
- Modify: `src/hyprbind/integrations/github_fetcher.py`
- Create: `tests/integrations/test_github_fetcher_async.py`

**Step 1: Write the failing test**

Create `tests/integrations/test_github_fetcher_async.py`:

```python
"""Tests for async GitHub fetcher operations."""

import pytest
import threading
from unittest.mock import patch, MagicMock
from typing import Dict, Any

from hyprbind.integrations.github_fetcher import GitHubFetcher


class TestAsyncFetcher:
    """Tests for async fetch operations."""

    def test_fetch_profile_async_calls_callback(self):
        """Test async fetch calls callback with result."""
        result_holder = {"called": False, "result": None}
        event = threading.Event()

        def callback(result: Dict[str, Any]) -> None:
            result_holder["called"] = True
            result_holder["result"] = result
            event.set()

        with patch.object(GitHubFetcher, '_make_request') as mock_request:
            mock_request.return_value = {
                "success": True,
                "data": [{"name": "repo1", "description": "test", "stargazers_count": 10, "html_url": "http://test"}]
            }

            GitHubFetcher.fetch_profile_async("testuser", callback)

            # Wait for callback (max 2 seconds)
            event.wait(timeout=2.0)

        assert result_holder["called"], "Callback was not called"
        assert result_holder["result"]["success"]
        assert "repos" in result_holder["result"]

    def test_fetch_profile_async_handles_error(self):
        """Test async fetch handles errors gracefully."""
        result_holder = {"called": False, "result": None}
        event = threading.Event()

        def callback(result: Dict[str, Any]) -> None:
            result_holder["called"] = True
            result_holder["result"] = result
            event.set()

        with patch.object(GitHubFetcher, '_make_request') as mock_request:
            mock_request.return_value = {"success": False, "message": "Network error"}

            GitHubFetcher.fetch_profile_async("testuser", callback)

            event.wait(timeout=2.0)

        assert result_holder["called"]
        assert not result_holder["result"]["success"]
        assert "message" in result_holder["result"]

    def test_fetch_profile_async_validates_username(self):
        """Test async fetch validates username before network call."""
        result_holder = {"called": False, "result": None}
        event = threading.Event()

        def callback(result: Dict[str, Any]) -> None:
            result_holder["called"] = True
            result_holder["result"] = result
            event.set()

        # Invalid username (contains special chars)
        GitHubFetcher.fetch_profile_async("invalid@user!", callback)

        event.wait(timeout=2.0)

        assert result_holder["called"]
        assert not result_holder["result"]["success"]
        assert "Invalid username" in result_holder["result"]["message"]

    def test_download_config_async_calls_callback(self):
        """Test async download calls callback with content."""
        result_holder = {"called": False, "result": None}
        event = threading.Event()

        def callback(result: Dict[str, Any]) -> None:
            result_holder["called"] = True
            result_holder["result"] = result
            event.set()

        with patch.object(GitHubFetcher, '_make_request') as mock_request:
            import base64
            content = base64.b64encode(b"bind = SUPER, Q, killactive").decode()
            mock_request.return_value = {
                "success": True,
                "data": {"encoding": "base64", "content": content}
            }

            GitHubFetcher.download_config_async("user", "repo", "path/to/config.conf", callback)

            event.wait(timeout=2.0)

        assert result_holder["called"]
        assert result_holder["result"]["success"]
        assert "content" in result_holder["result"]
```

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=/home/komi/repos/hyprbind/worktrees/dev/src /home/komi/repos/hyprbind/worktrees/dev/.venv/bin/python -m pytest tests/integrations/test_github_fetcher_async.py::TestAsyncFetcher::test_fetch_profile_async_calls_callback -v`

Expected: FAIL with "AttributeError: type object 'GitHubFetcher' has no attribute 'fetch_profile_async'"

**Step 3: Implement async methods**

Add to `src/hyprbind/integrations/github_fetcher.py`:

```python
import threading
from typing import Callable

# Add these methods to GitHubFetcher class:

    @staticmethod
    def fetch_profile_async(
        username: str,
        callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Fetch GitHub profile asynchronously.

        Runs network request in background thread and calls callback
        with result on completion. Safe to call from GTK main thread.

        Args:
            username: GitHub username
            callback: Function to call with result dict when complete
        """
        def worker():
            result = GitHubFetcher.fetch_profile(username)
            callback(result)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    @staticmethod
    def find_config_files_async(
        username: str,
        repo: str,
        callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Find config files asynchronously.

        Args:
            username: GitHub username
            repo: Repository name
            callback: Function to call with result
        """
        def worker():
            result = GitHubFetcher.find_config_files(username, repo)
            callback(result)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    @staticmethod
    def download_config_async(
        username: str,
        repo: str,
        path: str,
        callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Download config file asynchronously.

        Args:
            username: GitHub username
            repo: Repository name
            path: Path to config file
            callback: Function to call with result
        """
        def worker():
            result = GitHubFetcher.download_config(username, repo, path)
            callback(result)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
```

**Step 4: Run tests to verify they pass**

Run: `PYTHONPATH=/home/komi/repos/hyprbind/worktrees/dev/src /home/komi/repos/hyprbind/worktrees/dev/.venv/bin/python -m pytest tests/integrations/test_github_fetcher_async.py -v`

Expected: PASS

**Step 5: Commit**

```bash
cd /home/komi/repos/hyprbind/worktrees/dev && git add src/hyprbind/integrations/github_fetcher.py tests/integrations/test_github_fetcher_async.py && git commit -m "feat(github): add async fetch methods with callback pattern"
```

---

### Task 6: Update CommunityTab to Use Async Fetching

**Files:**
- Modify: `src/hyprbind/ui/community_tab.py`

**Step 1: Add loading state and async import**

Update `_on_import_clicked` in `src/hyprbind/ui/community_tab.py`:

```python
    def _on_import_clicked(self, button: Gtk.Button) -> None:
        """Handle import button click - async with progress feedback.

        Args:
            button: The import button
        """
        from gi.repository import GLib
        from hyprbind.integrations.github_fetcher import GitHubFetcher

        selected_item = self.selection_model.get_selected_item()

        if not selected_item:
            return

        # Disable button and show loading state
        button.set_sensitive(False)
        button.set_label("Fetching...")

        username = selected_item.username
        repo = selected_item.repo

        def on_files_found(result):
            """Callback when config files are found."""
            # Run UI updates on main thread
            GLib.idle_add(self._handle_files_result, result, username, repo, button)

        # Start async fetch
        GitHubFetcher.find_config_files_async(username, repo, on_files_found)

    def _handle_files_result(
        self,
        result: dict,
        username: str,
        repo: str,
        button: Gtk.Button
    ) -> bool:
        """Handle async file search result on main thread.

        Args:
            result: Result from GitHubFetcher
            username: GitHub username
            repo: Repository name
            button: Import button to restore

        Returns:
            False to remove idle callback
        """
        from gi.repository import GLib
        from hyprbind.integrations.github_fetcher import GitHubFetcher

        if not result["success"]:
            self._show_error_dialog("Fetch Failed", result.get("message", "Unknown error"))
            button.set_sensitive(True)
            button.set_label("Import Configuration")
            return False

        files = result.get("files", [])
        if not files:
            self._show_error_dialog("No Config Found", "No Hyprland config files found in repository.")
            button.set_sensitive(True)
            button.set_label("Import Configuration")
            return False

        # Use first config file found
        config_path = files[0]
        button.set_label(f"Downloading {config_path}...")

        def on_download_complete(download_result):
            GLib.idle_add(self._handle_download_result, download_result, button)

        GitHubFetcher.download_config_async(username, repo, config_path, on_download_complete)
        return False

    def _handle_download_result(self, result: dict, button: Gtk.Button) -> bool:
        """Handle async download result on main thread.

        Args:
            result: Download result from GitHubFetcher
            button: Import button to restore

        Returns:
            False to remove idle callback
        """
        button.set_sensitive(True)
        button.set_label("Import Configuration")

        if not result["success"]:
            self._show_error_dialog("Download Failed", result.get("message", "Unknown error"))
            return False

        content = result.get("content", "")
        if not content:
            self._show_error_dialog("Empty Config", "Downloaded config file is empty.")
            return False

        # Show preview dialog
        self._show_import_preview_dialog(content, result.get("path", "config"))
        return False

    def _show_import_preview_dialog(self, content: str, path: str) -> None:
        """Show preview of config before importing.

        Args:
            content: Config file content
            path: Path to config file
        """
        from hyprbind.parsers.config_parser import ConfigParser

        # Parse to count bindings
        try:
            parsed = ConfigParser.parse_string(content)
            binding_count = len(parsed.get_all_bindings())
        except Exception:
            binding_count = "unknown"

        dialog = Adw.MessageDialog.new(self.get_root())
        dialog.set_heading("Import Configuration")
        dialog.set_body(
            f"Found {binding_count} bindings in {path}.\n\n"
            f"Import these bindings into your configuration?\n\n"
            f"Note: Conflicting bindings will be skipped."
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("import", "Import")
        dialog.set_response_appearance("import", Adw.ResponseAppearance.SUGGESTED)
        dialog.connect("response", self._on_import_dialog_response, content)
        dialog.present()

    def _on_import_dialog_response(
        self,
        dialog: Adw.MessageDialog,
        response: str,
        content: str
    ) -> None:
        """Handle import confirmation dialog response.

        Args:
            dialog: The dialog
            response: Response ID
            content: Config content to import
        """
        if response != "import":
            return

        # Get config manager from main window
        main_window = self.get_root()
        if not hasattr(main_window, "config_manager"):
            self._show_error_dialog("Error", "Cannot access configuration manager.")
            return

        from hyprbind.integrations.github_fetcher import GitHubFetcher

        result = GitHubFetcher.import_to_config(content, main_window.config_manager)

        if result.success:
            self._show_success_dialog("Import Complete", result.message)
        else:
            self._show_error_dialog("Import Failed", result.message)

    def _show_error_dialog(self, heading: str, message: str) -> None:
        """Show error dialog.

        Args:
            heading: Dialog heading
            message: Error message
        """
        dialog = Adw.MessageDialog.new(self.get_root())
        dialog.set_heading(heading)
        dialog.set_body(message)
        dialog.add_response("ok", "OK")
        dialog.present()

    def _show_success_dialog(self, heading: str, message: str) -> None:
        """Show success dialog.

        Args:
            heading: Dialog heading
            message: Success message
        """
        dialog = Adw.MessageDialog.new(self.get_root())
        dialog.set_heading(heading)
        dialog.set_body(message)
        dialog.add_response("ok", "OK")
        dialog.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)
        dialog.present()
```

**Step 2: Run the full test suite**

Run: `PYTHONPATH=/home/komi/repos/hyprbind/worktrees/dev/src /home/komi/repos/hyprbind/worktrees/dev/.venv/bin/python -m pytest tests/ -v --tb=short`

Expected: PASS

**Step 3: Commit**

```bash
cd /home/komi/repos/hyprbind/worktrees/dev && git add src/hyprbind/ui/community_tab.py && git commit -m "feat(ui): async GitHub import with progress feedback"
```

---

### Task 7: Final Integration Test

**Files:**
- Test: Full test suite

**Step 1: Run complete test suite**

Run: `PYTHONPATH=/home/komi/repos/hyprbind/worktrees/dev/src /home/komi/repos/hyprbind/worktrees/dev/.venv/bin/python -m pytest tests/ -v --tb=short`

Expected: All tests PASS

**Step 2: Run with coverage**

Run: `PYTHONPATH=/home/komi/repos/hyprbind/worktrees/dev/src /home/komi/repos/hyprbind/worktrees/dev/.venv/bin/python -m pytest tests/ --cov=hyprbind --cov-report=term-missing`

Expected: Coverage maintained or improved

**Step 3: Final commit**

```bash
cd /home/komi/repos/hyprbind/worktrees/dev && git add -A && git commit -m "test: verify all performance fixes work together"
```

---

## Summary

| Task | Description | Complexity |
|------|-------------|-----------|
| 1 | Add conflict_key property to Binding | Low |
| 2 | Add binding index to Config | Medium |
| 3 | Update ConflictDetector to use index | Low |
| 4 | Update ConfigManager for index | Low |
| 5 | Create async GitHubFetcher methods | Medium |
| 6 | Update CommunityTab async import | Medium |
| 7 | Final integration testing | Low |

**Total estimated implementation time:** 7 tasks, each 2-5 minutes = ~30 minutes

**Performance impact:**
- Conflict detection: O(n²) → O(n) for bulk imports (100x faster)
- Network operations: Blocking → Non-blocking (responsive UI)
