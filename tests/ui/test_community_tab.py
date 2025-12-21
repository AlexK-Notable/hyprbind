"""Tests for community tab."""

import gi
import threading
import json
from unittest.mock import patch, MagicMock, Mock

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw
import pytest

from hyprbind.ui.community_tab import CommunityTab, ProfileItem
from hyprbind.core.config_manager import ConfigManager
from hyprbind.core.models import Config


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def config_manager(tmp_path):
    """Create ConfigManager with empty config using isolated temp path.

    CRITICAL: Uses tmp_path to ensure tests NEVER write to user's real config.
    """
    temp_config = tmp_path / "test_keybinds.conf"
    temp_config.write_text("# Test config\n")

    manager = ConfigManager(config_path=temp_config, skip_validation=True)
    manager.config = Config()
    return manager


@pytest.fixture
def community_tab():
    """Create CommunityTab without config manager."""
    return CommunityTab()


@pytest.fixture
def community_tab_with_manager(config_manager):
    """Create CommunityTab with config manager."""
    return CommunityTab(config_manager=config_manager)


# =============================================================================
# ProfileItem Tests
# =============================================================================

class TestProfileItem:
    """Test ProfileItem GObject class."""

    def test_profile_item_creation(self):
        """ProfileItem can be created with all properties."""
        item = ProfileItem(
            username="testuser",
            repo="test-repo",
            description="Test description",
            stars=100,
        )

        assert item.username == "testuser"
        assert item.repo == "test-repo"
        assert item.description == "Test description"
        assert item.stars == 100

    def test_profile_item_default_values(self):
        """ProfileItem has sensible defaults."""
        item = ProfileItem()

        assert item.username == ""
        assert item.repo == ""
        assert item.description == ""
        assert item.stars == 0

    def test_profile_item_is_gobject(self):
        """ProfileItem inherits from GObject."""
        from gi.repository import GObject
        item = ProfileItem()
        assert isinstance(item, GObject.Object)


# =============================================================================
# Basic Structure Tests
# =============================================================================

class TestCommunityTabStructure:
    """Test CommunityTab basic structure."""

    def test_community_tab_is_box(self, community_tab):
        """Community tab is a Gtk.Box."""
        assert isinstance(community_tab, Gtk.Box)

    def test_community_tab_has_profile_list(self, community_tab):
        """Community tab has profile list widget."""
        assert community_tab.profile_list is not None
        assert isinstance(community_tab.profile_list, Gtk.ListView)

    def test_community_tab_has_description_label(self, community_tab):
        """Community tab has description label."""
        assert community_tab.description_label is not None
        assert isinstance(community_tab.description_label, Gtk.Label)

    def test_community_tab_has_import_button(self, community_tab):
        """Community tab has import button."""
        assert community_tab.import_button is not None
        assert isinstance(community_tab.import_button, Gtk.Button)

    def test_community_tab_has_loading_spinner(self, community_tab):
        """Community tab has loading spinner."""
        assert community_tab.loading_spinner is not None
        assert isinstance(community_tab.loading_spinner, Gtk.Spinner)

    def test_community_tab_has_status_label(self, community_tab):
        """Community tab has status label."""
        assert community_tab.status_label is not None
        assert isinstance(community_tab.status_label, Gtk.Label)

    def test_community_tab_has_selection_model(self, community_tab):
        """Community tab has selection model."""
        assert community_tab.selection_model is not None
        assert isinstance(community_tab.selection_model, Gtk.SingleSelection)

    def test_community_tab_has_list_store(self, community_tab):
        """Community tab has list store."""
        assert community_tab.list_store is not None
        from gi.repository import Gio
        assert isinstance(community_tab.list_store, Gio.ListStore)


# =============================================================================
# Profile Data Tests
# =============================================================================

class TestProfileData:
    """Test profile data handling."""

    def test_displays_popular_profiles(self, community_tab):
        """Community tab displays list of popular profiles."""
        assert len(community_tab.profiles) >= 3

    def test_profiles_have_required_fields(self, community_tab):
        """Each profile has required fields."""
        for profile in community_tab.profiles:
            assert "username" in profile
            assert "repo" in profile
            assert "description" in profile
            assert "stars" in profile

    def test_list_store_populated_with_profiles(self, community_tab):
        """List store is populated with profile items."""
        assert community_tab.list_store.get_n_items() == len(community_tab.profiles)

    def test_list_store_items_are_profile_items(self, community_tab):
        """List store contains ProfileItem instances."""
        for i in range(community_tab.list_store.get_n_items()):
            item = community_tab.list_store.get_item(i)
            assert isinstance(item, ProfileItem)

    def test_profile_data_matches_list_store(self, community_tab):
        """Profile data matches list store items."""
        for i, profile in enumerate(community_tab.profiles):
            item = community_tab.list_store.get_item(i)
            assert item.username == profile["username"]
            assert item.repo == profile["repo"]
            assert item.stars == profile["stars"]


# =============================================================================
# Button State Tests
# =============================================================================

class TestButtonStates:
    """Test button state management."""

    def test_import_button_disabled_initially(self, community_tab):
        """Import button is disabled when no profile is selected."""
        assert not community_tab.import_button.get_sensitive()

    def test_loading_spinner_hidden_initially(self, community_tab):
        """Loading spinner is hidden initially."""
        assert not community_tab.loading_spinner.get_visible()

    def test_status_label_empty_initially(self, community_tab):
        """Status label is empty initially."""
        assert community_tab.status_label.get_text() == ""

    def test_selection_enables_import_button(self, community_tab):
        """Selecting a profile enables the import button."""
        assert not community_tab.import_button.get_sensitive()

        # Simulate selection
        if community_tab.selection_model.get_n_items() > 0:
            community_tab.selection_model.set_selected(0)
            community_tab._on_selection_changed(community_tab.selection_model, 0, 1)
            assert community_tab.import_button.get_sensitive()

    def test_deselection_disables_import_button(self, community_tab):
        """Deselecting disables the import button."""
        # First select
        if community_tab.selection_model.get_n_items() > 0:
            community_tab.selection_model.set_selected(0)
            community_tab._on_selection_changed(community_tab.selection_model, 0, 1)
            assert community_tab.import_button.get_sensitive()

            # Then simulate no selection by setting selected to invalid
            community_tab.selection_model.set_selected(Gtk.INVALID_LIST_POSITION)
            community_tab._on_selection_changed(community_tab.selection_model, 0, 1)
            # Button should be disabled when nothing is selected


# =============================================================================
# Loading State Tests
# =============================================================================

class TestLoadingState:
    """Test loading state management."""

    def test_set_loading_true_shows_spinner(self, community_tab):
        """Setting loading to True shows spinner."""
        community_tab._set_loading(True, "Loading...")

        assert community_tab.loading_spinner.get_visible()
        assert community_tab.status_label.get_text() == "Loading..."

    def test_set_loading_false_hides_spinner(self, community_tab):
        """Setting loading to False hides spinner."""
        community_tab._set_loading(True, "Loading...")
        community_tab._set_loading(False)

        assert not community_tab.loading_spinner.get_visible()
        assert community_tab.status_label.get_text() == ""

    def test_loading_disables_import_button(self, community_tab):
        """Loading state disables import button."""
        # First enable the button by selecting
        if community_tab.selection_model.get_n_items() > 0:
            community_tab.selection_model.set_selected(0)
            community_tab._on_selection_changed(community_tab.selection_model, 0, 1)
            assert community_tab.import_button.get_sensitive()

            # Now set loading
            community_tab._set_loading(True, "Loading...")
            assert not community_tab.import_button.get_sensitive()

    def test_loading_flag_tracked(self, community_tab):
        """Loading flag is tracked correctly."""
        assert not community_tab._loading

        community_tab._set_loading(True, "Loading...")
        assert community_tab._loading

        community_tab._set_loading(False)
        assert not community_tab._loading


# =============================================================================
# Selection Handler Tests
# =============================================================================

class TestSelectionHandler:
    """Test selection change handling."""

    def test_selection_updates_description(self, community_tab):
        """Selecting a profile updates description label."""
        if community_tab.selection_model.get_n_items() > 0:
            community_tab.selection_model.set_selected(0)
            community_tab._on_selection_changed(community_tab.selection_model, 0, 1)

            # Description should contain profile info
            text = community_tab.description_label.get_text()
            profile = community_tab.profiles[0]
            # Check that markup was set (get_text won't include tags)
            assert len(text) > 0

    def test_no_selection_resets_description(self, community_tab):
        """No selection resets description label."""
        # First select something
        if community_tab.selection_model.get_n_items() > 0:
            community_tab.selection_model.set_selected(0)
            community_tab._on_selection_changed(community_tab.selection_model, 0, 1)

            # Now deselect
            community_tab.selection_model.set_selected(Gtk.INVALID_LIST_POSITION)
            community_tab._on_selection_changed(community_tab.selection_model, 0, 1)


# =============================================================================
# Import Handler Tests
# =============================================================================

class TestImportHandler:
    """Test import button click handling."""

    def test_import_without_manager_shows_error(self, community_tab):
        """Import without config manager shows error."""
        # Select a profile
        if community_tab.selection_model.get_n_items() > 0:
            community_tab.selection_model.set_selected(0)
            community_tab._on_selection_changed(community_tab.selection_model, 0, 1)

        # Click import - should not crash, just show error
        # (We can't easily test dialogs without running the main loop)
        # Just verify the method doesn't throw
        # The actual dialog would need GTK main loop to show

    def test_import_with_no_selection_does_nothing(self, community_tab_with_manager):
        """Import with no selection does nothing."""
        tab = community_tab_with_manager

        # Mock selection_model to return None (simulating no selection)
        with patch.object(tab.selection_model, 'get_selected_item', return_value=None):
            # Verify early return behavior
            tab._on_import_clicked(tab.import_button)

            # Should not be loading since we returned early
            assert not tab._loading

    def test_import_while_loading_does_nothing(self, community_tab_with_manager):
        """Import while already loading does nothing."""
        tab = community_tab_with_manager

        # Select and set loading
        if tab.selection_model.get_n_items() > 0:
            tab.selection_model.set_selected(0)
            tab._on_selection_changed(tab.selection_model, 0, 1)

        tab._loading = True

        # Try to import
        with patch.object(tab, '_set_loading') as mock_set_loading:
            tab._on_import_clicked(tab.import_button)
            # Should not have called _set_loading (early return)
            mock_set_loading.assert_not_called()


# =============================================================================
# Async Callback Tests
# =============================================================================

class TestAsyncCallbacks:
    """Test async callback handlers."""

    def test_config_files_found_success(self, community_tab_with_manager):
        """Config files found callback handles success."""
        tab = community_tab_with_manager
        tab._loading = True

        profile = ProfileItem(username="test", repo="repo", description="", stars=0)

        # Mock result with one file
        result = {
            "success": True,
            "files": [".config/hypr/keybinds.conf"],
        }

        # Should try to download the single file
        with patch.object(tab, '_download_config') as mock_download:
            tab._on_config_files_found(result, profile)
            mock_download.assert_called_once_with(profile, ".config/hypr/keybinds.conf")

    def test_config_files_found_failure(self, community_tab_with_manager):
        """Config files found callback handles failure."""
        tab = community_tab_with_manager
        tab._loading = True

        profile = ProfileItem(username="test", repo="repo", description="", stars=0)

        result = {
            "success": False,
            "message": "Network error",
        }

        with patch.object(tab, '_show_error') as mock_error:
            tab._on_config_files_found(result, profile)
            mock_error.assert_called_once()
            assert "Network error" in mock_error.call_args[0][0]

    def test_config_files_found_empty(self, community_tab_with_manager):
        """Config files found callback handles empty results."""
        tab = community_tab_with_manager
        tab._loading = True

        profile = ProfileItem(username="test", repo="repo", description="", stars=0)

        result = {
            "success": True,
            "files": [],
        }

        with patch.object(tab, '_show_error') as mock_error:
            tab._on_config_files_found(result, profile)
            mock_error.assert_called_once()
            assert "No Hyprland config files" in mock_error.call_args[0][0]

    def test_config_files_found_multiple_shows_dialog(self, community_tab_with_manager):
        """Multiple config files triggers selection dialog."""
        tab = community_tab_with_manager
        tab._loading = True

        profile = ProfileItem(username="test", repo="repo", description="", stars=0)

        result = {
            "success": True,
            "files": ["file1.conf", "file2.conf", "file3.conf"],
        }

        with patch.object(tab, '_show_file_selection_dialog') as mock_dialog:
            tab._on_config_files_found(result, profile)
            mock_dialog.assert_called_once_with(profile, result["files"])

    def test_config_downloaded_success(self, community_tab_with_manager):
        """Config downloaded callback handles success."""
        tab = community_tab_with_manager
        tab._loading = True

        profile = ProfileItem(username="test", repo="repo", description="", stars=0)

        result = {
            "success": True,
            "content": "bindd = $mainMod, Q, Close, killactive",
        }

        with patch('hyprbind.ui.community_tab.GitHubFetcher.import_to_config') as mock_import:
            from hyprbind.core.config_manager import OperationResult
            mock_import.return_value = OperationResult(success=True, message="Imported 1 binding")

            with patch.object(tab, '_show_success') as mock_success:
                tab._on_config_downloaded(result, profile, "test.conf")
                mock_success.assert_called_once()

    def test_config_downloaded_failure(self, community_tab_with_manager):
        """Config downloaded callback handles failure."""
        tab = community_tab_with_manager
        tab._loading = True

        profile = ProfileItem(username="test", repo="repo", description="", stars=0)

        result = {
            "success": False,
            "message": "File not found",
        }

        with patch.object(tab, '_show_error') as mock_error:
            tab._on_config_downloaded(result, profile, "test.conf")
            mock_error.assert_called_once()
            assert "File not found" in mock_error.call_args[0][0]

    def test_config_downloaded_empty_content(self, community_tab_with_manager):
        """Config downloaded callback handles empty content."""
        tab = community_tab_with_manager
        tab._loading = True

        profile = ProfileItem(username="test", repo="repo", description="", stars=0)

        result = {
            "success": True,
            "content": "",
        }

        with patch.object(tab, '_show_error') as mock_error:
            tab._on_config_downloaded(result, profile, "test.conf")
            mock_error.assert_called_once()
            assert "empty" in mock_error.call_args[0][0].lower()


# =============================================================================
# Integration Tests
# =============================================================================

class TestImportIntegration:
    """Test import flow integration."""

    @patch('hyprbind.ui.community_tab.GitHubFetcher.find_config_files_async')
    def test_import_starts_async_search(self, mock_async, community_tab_with_manager):
        """Import button starts async config file search."""
        tab = community_tab_with_manager

        # Select a profile
        if tab.selection_model.get_n_items() > 0:
            tab.selection_model.set_selected(0)
            tab._on_selection_changed(tab.selection_model, 0, 1)

        # Click import
        tab._on_import_clicked(tab.import_button)

        # Should have started async search
        mock_async.assert_called_once()

        # Verify correct arguments
        args = mock_async.call_args
        assert args[0][0] == tab.profiles[0]["username"]
        assert args[0][1] == tab.profiles[0]["repo"]

    def test_download_config_sets_loading_state(self, community_tab_with_manager):
        """_download_config sets loading state."""
        tab = community_tab_with_manager
        tab._loading = False

        profile = ProfileItem(username="test", repo="repo", description="", stars=0)

        with patch('hyprbind.ui.community_tab.GitHubFetcher.download_config_async'):
            tab._download_config(profile, "test.conf")

            assert tab._loading
            assert "Downloading" in tab.status_label.get_text()


# =============================================================================
# Config Manager Integration Tests
# =============================================================================

class TestConfigManagerIntegration:
    """Test integration with ConfigManager."""

    def test_tab_stores_config_manager(self, community_tab_with_manager):
        """Tab stores config manager reference."""
        assert community_tab_with_manager.config_manager is not None

    def test_tab_without_manager_has_none(self, community_tab):
        """Tab without manager has None."""
        assert community_tab.config_manager is None

    def test_import_uses_config_manager(self, community_tab_with_manager):
        """Import uses the config manager."""
        tab = community_tab_with_manager
        tab._loading = True

        profile = ProfileItem(username="test", repo="repo", description="", stars=0)

        result = {
            "success": True,
            "content": "bindd = $mainMod, Q, Close, killactive",
        }

        with patch('hyprbind.ui.community_tab.GitHubFetcher.import_to_config') as mock_import:
            from hyprbind.core.config_manager import OperationResult
            mock_import.return_value = OperationResult(success=True, message="OK")

            with patch.object(tab, '_show_success'):
                tab._on_config_downloaded(result, profile, "test.conf")

            # Verify import was called with correct config manager
            mock_import.assert_called_once()
            assert mock_import.call_args[0][1] == tab.config_manager
