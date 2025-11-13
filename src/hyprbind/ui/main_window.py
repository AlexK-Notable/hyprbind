"""Main application window."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib
from pathlib import Path
from typing import Any, Optional
import sys
import threading


def _get_ui_file_path() -> Path:
    """
    Get path to UI file, works both in development and when installed.

    Returns:
        Path to main_window.ui file
    """
    # Try development path first (for running from git repo)
    dev_path = Path(__file__).parent.parent.parent.parent / "data" / "ui" / "main_window.ui"
    if dev_path.exists():
        return dev_path

    # Try installed package data path
    try:
        from importlib.resources import files
        ui_file = files("hyprbind").parent / "data" / "ui" / "main_window.ui"
        if ui_file.exists():
            return ui_file
    except (ImportError, AttributeError):
        pass

    # Fallback: check common installation locations
    possible_paths = [
        Path(sys.prefix) / "share" / "hyprbind" / "ui" / "main_window.ui",
        Path.home() / ".local" / "share" / "hyprbind" / "ui" / "main_window.ui",
    ]

    for path in possible_paths:
        if path.exists():
            return path

    # If all else fails, return dev path and let it fail with clear error
    raise FileNotFoundError(
        f"Could not find main_window.ui. Tried:\n"
        f"  - Development: {dev_path}\n"
        f"  - Package data: <importlib.resources>\n"
        f"  - System: {possible_paths}\n"
        f"Please ensure the package is properly installed or run from git repository."
    )


_UI_FILE = _get_ui_file_path()


@Gtk.Template(filename=str(_UI_FILE))
class MainWindow(Adw.ApplicationWindow):
    """Main HyprBind application window.

    This window uses GTK Builder template for UI definition.
    """

    __gtype_name__ = "HyprBindMainWindow"

    # Template children with type annotations
    main_content: Gtk.Box = Gtk.Template.Child()
    header_bar: Adw.HeaderBar = Gtk.Template.Child()
    chezmoi_banner: Adw.Banner = Gtk.Template.Child()
    tab_view: Adw.TabView = Gtk.Template.Child()
    loading_box: Gtk.Box = Gtk.Template.Child()
    loading_spinner: Gtk.Spinner = Gtk.Template.Child()

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the main window."""
        super().__init__(**kwargs)

        # Initialize ConfigManager
        from hyprbind.core.config_manager import ConfigManager
        self.config_manager = ConfigManager()

        # Setup Chezmoi banner
        self._setup_chezmoi_banner()

        # Setup tabs
        self._setup_tabs()

        # Register as observer for config changes
        self.config_manager.add_observer(self._on_config_changed)

        # Load config asynchronously
        self._load_config_async()

    def _setup_chezmoi_banner(self) -> None:
        """Setup the Chezmoi banner and connect its signals."""
        self.chezmoi_banner.connect("button-clicked", self._on_chezmoi_learn_more)

    def _check_chezmoi_management(self) -> None:
        """Check if the config file is managed by Chezmoi and show banner if it is."""
        from hyprbind.integrations.chezmoi import ChezmoiIntegration

        config_path = self.config_manager.config_path
        if config_path and ChezmoiIntegration.is_managed(config_path):
            source_path = ChezmoiIntegration.get_source_path(config_path)
            if source_path:
                # Update banner message with source path
                self.chezmoi_banner.set_title(
                    f"This file is managed by Chezmoi. "
                    f"Source: {source_path.name}"
                )
                self.chezmoi_banner.set_revealed(True)

    def _on_chezmoi_learn_more(self, banner: Adw.Banner) -> None:
        """Show dialog with Chezmoi workflow information."""
        from hyprbind.integrations.chezmoi import ChezmoiIntegration

        config_path = self.config_manager.config_path
        if not config_path:
            return

        source_path = ChezmoiIntegration.get_source_path(config_path)

        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading("Chezmoi Integration")

        body_text = (
            "This configuration file is managed by Chezmoi.\n\n"
            "Recommended workflow:\n"
            "1. Edit the source file in Chezmoi:\n"
            f"   chezmoi edit {config_path}\n\n"
            "2. Apply changes:\n"
            "   chezmoi apply\n\n"
            "Or edit directly in HyprBind, but remember to run:\n"
            "   chezmoi re-add {config_path}"
        )

        if source_path:
            body_text += f"\n\nSource file location:\n{source_path}"

        dialog.set_body(body_text)
        dialog.add_response("ok", "OK")
        dialog.present()

    def _setup_tabs(self) -> None:
        """Create tab structure with placeholders."""
        # Import tabs
        from hyprbind.ui.editor_tab import EditorTab
        from hyprbind.ui.cheatsheet_tab import CheatsheetTab
        from hyprbind.ui.community_tab import CommunityTab
        from hyprbind.ui.reference_tab import ReferenceTab

        # Editor tab (fully implemented)
        editor_tab = EditorTab(self.config_manager)
        editor_page = self.tab_view.append(editor_tab)
        editor_page.set_title("Editor")
        self.editor_tab = editor_tab  # Store reference

        # Community tab (fully implemented)
        community_tab = CommunityTab()
        community_page = self.tab_view.append(community_tab)
        community_page.set_title("Community")
        self.community_tab = community_tab  # Store reference

        # Cheatsheet tab (fully implemented)
        cheatsheet_tab = CheatsheetTab(self.config_manager)
        cheatsheet_page = self.tab_view.append(cheatsheet_tab)
        cheatsheet_page.set_title("Cheatsheet")
        self.cheatsheet_tab = cheatsheet_tab  # Store reference

        # Reference tab (fully implemented)
        reference_tab = ReferenceTab()
        reference_page = self.tab_view.append(reference_tab)
        reference_page.set_title("Reference")
        self.reference_tab = reference_tab  # Store reference

    def _show_loading(self) -> None:
        """Show loading indicator."""
        self.loading_box.set_visible(True)

    def _hide_loading(self) -> None:
        """Hide loading indicator."""
        self.loading_box.set_visible(False)

    def _load_config_async(self) -> None:
        """Load config in background thread."""
        self._show_loading()

        def load_thread():
            """Background thread function."""
            try:
                self.config_manager.load()
                GLib.idle_add(self._on_config_loaded)
            except Exception as e:
                GLib.idle_add(self._on_config_load_error, str(e))

        thread = threading.Thread(target=load_thread, daemon=True)
        thread.start()

    def _on_config_loaded(self) -> None:
        """Called on main thread after config loads successfully."""
        self._hide_loading()
        # Check if config is managed by Chezmoi
        self._check_chezmoi_management()
        # Tabs will be notified via observer pattern
        # For now, they're just placeholders
        return False  # Don't call again

    def _on_config_load_error(self, error_message: str) -> None:
        """Called on main thread if config loading fails."""
        self._hide_loading()
        # Show error dialog
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading("Configuration Load Error")
        dialog.set_body(f"Failed to load configuration:\n{error_message}")
        dialog.add_response("ok", "OK")
        dialog.present()
        return False  # Don't call again

    def _on_config_changed(self) -> None:
        """Observer callback - called when config changes."""
        # For now, just print notification
        # Later tasks will implement tab refresh logic here
        print("Config changed notification received")

    def do_close_request(self) -> bool:
        """Handle window close request. Check for unsaved changes.

        Returns:
            True to prevent closing, False to allow closing
        """
        if self.config_manager.is_dirty():
            # Show confirmation dialog
            dialog = Adw.MessageDialog.new(self)
            dialog.set_heading("Unsaved Changes")
            dialog.set_body("You have unsaved changes. Do you want to save before closing?")
            dialog.add_response("cancel", "Cancel")
            dialog.add_response("discard", "Discard")
            dialog.add_response("save", "Save and Close")
            dialog.set_response_appearance("discard", Adw.ResponseAppearance.DESTRUCTIVE)
            dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)

            dialog.connect("response", self._on_close_dialog_response)
            dialog.present()
            return True  # Prevent close for now

        return False  # Allow close

    def _on_close_dialog_response(self, dialog: Adw.MessageDialog, response: str) -> None:
        """Handle close confirmation dialog response."""
        if response == "cancel":
            # Do nothing, window stays open
            pass
        elif response == "discard":
            # Close without saving
            self.destroy()
        elif response == "save":
            # Save and close
            result = self.config_manager.save()
            if result.success:
                self.destroy()
            else:
                # Show error
                error_dialog = Adw.MessageDialog.new(self)
                error_dialog.set_heading("Save Failed")
                error_dialog.set_body(f"Failed to save configuration:\n{result.message}")
                error_dialog.add_response("ok", "OK")
                error_dialog.present()
