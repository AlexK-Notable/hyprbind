"""Community tab for importing configs from popular GitHub profiles."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Gio, GObject, Adw
from typing import Dict, List, Any, Optional, Callable

from hyprbind.integrations.github_fetcher import GitHubFetcher
from hyprbind.core.config_manager import ConfigManager


class ProfileItem(GObject.Object):
    """Profile item for the community list."""

    # GObject properties
    username: str = GObject.Property(type=str, default="")
    repo: str = GObject.Property(type=str, default="")
    description: str = GObject.Property(type=str, default="")
    stars: int = GObject.Property(type=int, default=0)

    def __init__(
        self,
        username: str = "",
        repo: str = "",
        description: str = "",
        stars: int = 0,
    ) -> None:
        """Initialize profile item.

        Args:
            username: GitHub username
            repo: Repository name
            description: Profile description
            stars: Star count (approximate)
        """
        super().__init__()
        self.username = username
        self.repo = repo
        self.description = description
        self.stars = stars


class CommunityTab(Gtk.Box):
    """Tab for discovering and importing popular Hyprland configurations."""

    def __init__(self, config_manager: Optional[ConfigManager] = None) -> None:
        """Initialize community tab.

        Args:
            config_manager: ConfigManager for importing configs (optional for testing)
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.config_manager = config_manager
        self._loading = False

        # Popular Hyprland configurations from the community
        self.profiles: List[Dict[str, Any]] = [
            {
                "username": "hyprland",
                "repo": "Hyprland",
                "description": "Official Hyprland examples and configuration templates",
                "stars": 25000,
            },
            {
                "username": "end-4",
                "repo": "dots-hyprland",
                "description": "Beautiful Material You themed Hyprland rice with animations",
                "stars": 4200,
            },
            {
                "username": "prasanthrangan",
                "repo": "hyprdots",
                "description": "Modern Hyprland dotfiles with auto-install script",
                "stars": 7800,
            },
            {
                "username": "linuxmobile",
                "repo": "hyprland-dots",
                "description": "Minimalist Hyprland setup with catppuccin theme",
                "stars": 2100,
            },
            {
                "username": "notwidow",
                "repo": "hyprland",
                "description": "Clean Hyprland config with waybar integration",
                "stars": 950,
            },
            {
                "username": "SolDoesTech",
                "repo": "HyprV4",
                "description": "Comprehensive Hyprland V4 configuration with tutorials",
                "stars": 1200,
            },
            {
                "username": "JaKooLit",
                "repo": "Hyprland-Dots",
                "description": "Feature-rich Hyprland dotfiles with extensive customization",
                "stars": 3500,
            },
        ]

        # Create list store for profiles
        self.list_store = Gio.ListStore.new(ProfileItem)
        for profile in self.profiles:
            item = ProfileItem(
                username=profile["username"],
                repo=profile["repo"],
                description=profile["description"],
                stars=profile["stars"],
            )
            self.list_store.append(item)

        # Selection model
        self.selection_model = Gtk.SingleSelection.new(self.list_store)
        self.selection_model.connect("selection-changed", self._on_selection_changed)

        # Create profile list view
        self.profile_list = Gtk.ListView.new(self.selection_model, None)

        # Create factory for profile cards
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._on_factory_setup)
        factory.connect("bind", self._on_factory_bind)
        self.profile_list.set_factory(factory)

        # Header
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label="Community Configs"))
        header.add_css_class("flat")
        self.append(header)

        # Main content box
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_start(24)
        content.set_margin_end(24)
        content.set_margin_top(24)
        content.set_margin_bottom(24)

        # Info banner
        banner = Adw.Banner()
        banner.set_title("Discover Popular Hyprland Configurations")
        banner.set_revealed(True)
        content.append(banner)

        # Scrolled window for profile list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_min_content_height(300)
        scrolled.set_child(self.profile_list)
        content.append(scrolled)

        # Description area
        description_group = Adw.PreferencesGroup()
        description_group.set_title("Selected Configuration")
        description_group.set_description("Select a profile above to see details")

        self.description_label = Gtk.Label()
        self.description_label.set_wrap(True)
        self.description_label.set_xalign(0)
        self.description_label.set_markup("<i>No profile selected</i>")
        description_group.add(self.description_label)

        content.append(description_group)

        # Import button with loading spinner
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_halign(Gtk.Align.START)
        button_box.set_spacing(12)

        self.import_button = Gtk.Button(label="Import Configuration")
        self.import_button.add_css_class("suggested-action")
        self.import_button.set_sensitive(False)  # Disabled initially
        self.import_button.connect("clicked", self._on_import_clicked)
        button_box.append(self.import_button)

        # Loading spinner (hidden initially)
        self.loading_spinner = Gtk.Spinner()
        self.loading_spinner.set_visible(False)
        button_box.append(self.loading_spinner)

        # Status label for import progress
        self.status_label = Gtk.Label()
        self.status_label.set_xalign(0)
        self.status_label.add_css_class("dim-label")
        button_box.append(self.status_label)

        content.append(button_box)

        self.append(content)

    def _on_factory_setup(self, factory: Gtk.SignalListItemFactory, list_item: Gtk.ListItem) -> None:
        """Setup factory for profile list items.

        Args:
            factory: The factory
            list_item: The list item being setup
        """
        # Create profile card
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)

        # Header with username and stars
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        username_label = Gtk.Label()
        username_label.set_name("username")
        username_label.set_xalign(0)
        username_label.set_hexpand(True)
        username_label.add_css_class("heading")
        header_box.append(username_label)

        stars_label = Gtk.Label()
        stars_label.set_name("stars")
        stars_label.add_css_class("dim-label")
        header_box.append(stars_label)

        box.append(header_box)

        # Repo label
        repo_label = Gtk.Label()
        repo_label.set_name("repo")
        repo_label.set_xalign(0)
        repo_label.add_css_class("caption")
        box.append(repo_label)

        # Description
        desc_label = Gtk.Label()
        desc_label.set_name("description")
        desc_label.set_xalign(0)
        desc_label.set_wrap(True)
        desc_label.add_css_class("dim-label")
        box.append(desc_label)

        # Add separator
        separator = Gtk.Separator()
        box.append(separator)

        list_item.set_child(box)

    def _on_factory_bind(self, factory: Gtk.SignalListItemFactory, list_item: Gtk.ListItem) -> None:
        """Bind data to profile list item.

        Args:
            factory: The factory
            list_item: The list item being bound
        """
        profile = list_item.get_item()
        box = list_item.get_child()

        # Find labels by name
        header_box = box.get_first_child()
        username_label = header_box.get_first_child()
        stars_label = username_label.get_next_sibling()

        repo_label = header_box.get_next_sibling()
        desc_label = repo_label.get_next_sibling()

        # Set text
        username_label.set_text(profile.username)
        stars_label.set_text(f"★ {profile.stars:,}")
        repo_label.set_text(f"Repository: {profile.repo}")
        desc_label.set_text(profile.description)

    def _on_selection_changed(
        self, selection: Gtk.SingleSelection, position: int, n_items: int
    ) -> None:
        """Handle profile selection changes.

        Args:
            selection: The selection model
            position: Position of change
            n_items: Number of items changed
        """
        selected_item = selection.get_selected_item()

        if selected_item:
            # Enable import button
            self.import_button.set_sensitive(True)

            # Update description
            self.description_label.set_markup(
                f"<b>{selected_item.username}/{selected_item.repo}</b>\n\n"
                f"{selected_item.description}\n\n"
                f"<small>Stars: {selected_item.stars:,}</small>"
            )
        else:
            # Disable import button
            self.import_button.set_sensitive(False)
            self.description_label.set_markup("<i>No profile selected</i>")

    def _set_loading(self, loading: bool, status: str = "") -> None:
        """Set loading state for UI.

        Args:
            loading: Whether loading is in progress
            status: Status message to display
        """
        self._loading = loading
        self.import_button.set_sensitive(not loading and self.selection_model.get_selected_item() is not None)
        self.loading_spinner.set_visible(loading)
        if loading:
            self.loading_spinner.start()
        else:
            self.loading_spinner.stop()
        self.status_label.set_text(status)

    def _on_import_clicked(self, button: Gtk.Button) -> None:
        """Handle import button click.

        Args:
            button: The import button
        """
        selected_item = self.selection_model.get_selected_item()

        if not selected_item or self._loading:
            return

        # Check if config_manager is available
        if not self.config_manager:
            self._show_error("Configuration manager not available")
            return

        # Start async config file discovery
        self._set_loading(True, "Finding config files...")

        GitHubFetcher.find_config_files_async(
            selected_item.username,
            selected_item.repo,
            lambda result: self._on_config_files_found(result, selected_item),
        )

    def _on_config_files_found(self, result: Dict[str, Any], profile: ProfileItem) -> None:
        """Handle config files discovery result.

        Args:
            result: Result from GitHubFetcher.find_config_files_async
            profile: The profile being imported
        """
        if not result["success"]:
            self._set_loading(False)
            self._show_error(f"Failed to find config files: {result['message']}")
            return

        config_files = result.get("files", [])

        if not config_files:
            self._set_loading(False)
            self._show_error("No Hyprland config files found in this repository")
            return

        # If only one file, download it directly
        if len(config_files) == 1:
            self._download_config(profile, config_files[0])
            return

        # Multiple files - show selection dialog
        self._set_loading(False)
        self._show_file_selection_dialog(profile, config_files)

    def _show_file_selection_dialog(
        self, profile: ProfileItem, config_files: List[str]
    ) -> None:
        """Show dialog to select which config file to import.

        Args:
            profile: The profile being imported
            config_files: List of available config file paths
        """
        dialog = Adw.MessageDialog.new(self.get_root())
        dialog.set_heading("Select Config File")
        dialog.set_body(
            f"Found {len(config_files)} config file(s) in {profile.username}/{profile.repo}.\n"
            "Select the file to import:"
        )

        # Add a response for each file
        for i, path in enumerate(config_files[:5]):  # Limit to 5 files
            response_id = f"file_{i}"
            # Show just the filename for cleaner display
            filename = path.split("/")[-1]
            dialog.add_response(response_id, filename)

        dialog.add_response("cancel", "Cancel")
        dialog.set_response_appearance("cancel", Adw.ResponseAppearance.DESTRUCTIVE)

        def on_response(dialog, response):
            if response.startswith("file_"):
                index = int(response.split("_")[1])
                self._download_config(profile, config_files[index])

        dialog.connect("response", on_response)
        dialog.present()

    def _download_config(self, profile: ProfileItem, path: str) -> None:
        """Download and import a config file.

        Args:
            profile: The profile to download from
            path: Path to the config file
        """
        self._set_loading(True, f"Downloading {path.split('/')[-1]}...")

        GitHubFetcher.download_config_async(
            profile.username,
            profile.repo,
            path,
            lambda result: self._on_config_downloaded(result, profile, path),
        )

    def _on_config_downloaded(
        self, result: Dict[str, Any], profile: ProfileItem, path: str
    ) -> None:
        """Handle config download result.

        Args:
            result: Result from GitHubFetcher.download_config_async
            profile: The profile being imported
            path: Path of the downloaded file
        """
        if not result["success"]:
            self._set_loading(False)
            self._show_error(f"Failed to download config: {result['message']}")
            return

        content = result.get("content", "")
        if not content:
            self._set_loading(False)
            self._show_error("Downloaded config file is empty")
            return

        self._set_loading(True, "Importing bindings...")

        # Import the config content
        import_result = GitHubFetcher.import_to_config(content, self.config_manager)

        self._set_loading(False)

        if import_result.success:
            self._show_success(
                f"Import Complete",
                f"{import_result.message}\n\n"
                f"Source: {profile.username}/{profile.repo}/{path.split('/')[-1]}"
            )
        else:
            self._show_error(f"Import failed: {import_result.message}")

    def _show_error(self, message: str) -> None:
        """Show error dialog.

        Args:
            message: Error message to display
        """
        dialog = Adw.MessageDialog.new(self.get_root())
        dialog.set_heading("Import Error")
        dialog.set_body(message)
        dialog.add_response("ok", "OK")
        dialog.present()

    def _show_success(self, heading: str, message: str) -> None:
        """Show success dialog.

        Args:
            heading: Dialog heading
            message: Success message to display
        """
        dialog = Adw.MessageDialog.new(self.get_root())
        dialog.set_heading(heading)
        dialog.set_body(message)
        dialog.add_response("ok", "OK")
        dialog.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)
        dialog.present()
