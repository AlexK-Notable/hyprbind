# Task 9: Tab Navigation Structure (CORRECTED)
**Corrections Applied**: Async loading, observer pattern, dirty tracking, loading indicator

---

## Changes from Original

**Added to ConfigManager** (`src/hyprbind/core/config_manager.py`):
```python
from typing import List, Callable

class ConfigManager:
    def __init__(self, config_path: Optional[Path] = None) -> None:
        # ... existing code
        self._observers: List[Callable[[], None]] = []
        self._dirty = False

    def add_observer(self, callback: Callable[[], None]) -> None:
        """Register observer for config changes."""
        self._observers.append(callback)

    def remove_observer(self, callback: Callable[[], None]) -> None:
        """Unregister observer."""
        if callback in self._observers:
            self._observers.remove(callback)

    def _notify_observers(self) -> None:
        """Notify all observers of change."""
        for callback in self._observers:
            try:
                callback()
            except Exception as e:
                print(f"Observer error: {e}")

    def is_dirty(self) -> bool:
        """Check if config has unsaved changes."""
        return self._dirty

    # Update existing methods:
    def add_binding(self, binding: Binding) -> OperationResult:
        # ... existing logic
        if result.success:
            self._dirty = True
            self._notify_observers()
        return result

    def remove_binding(self, binding: Binding) -> OperationResult:
        # ... existing logic
        if result.success:
            self._dirty = True
            self._notify_observers()
        return result

    def update_binding(self, old: Binding, new: Binding) -> OperationResult:
        # ... existing logic
        if result.success:
            self._dirty = True
            self._notify_observers()
        return result

    def load(self) -> Optional[Config]:
        # ... existing logic
        if result:
            self._dirty = False
            self._notify_observers()
        return result

    def save(self, output_path: Optional[Path] = None) -> OperationResult:
        # ... existing logic (added in Task 15)
        if result.success:
            self._dirty = False
        return result
```

**MainWindow** (`src/hyprbind/ui/main_window.py`):
```python
import threading
from gi.repository import Gtk, Adw, GLib

class MainWindow(Adw.ApplicationWindow):
    # ... template binding

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        # Loading indicator
        self.loading_spinner = Gtk.Spinner()
        self.loading_spinner.set_size_request(48, 48)
        self.loading_spinner.set_halign(Gtk.Align.CENTER)
        self.loading_spinner.set_valign(Gtk.Align.CENTER)

        overlay = Gtk.Overlay()
        overlay.set_child(self.main_content)
        overlay.add_overlay(self.loading_spinner)

        # Replace main_content in window
        self.set_content(overlay)

        self._setup_tabs()

    def _setup_tabs(self) -> None:
        """Create tabs and load config asynchronously."""
        from hyprbind.core.config_manager import ConfigManager

        self.config_manager = ConfigManager()

        # Create tabs with empty config
        self.editor_tab = EditorTab(self.config_manager)
        self.tab_view.append(self.editor_tab).set_title("Editor")

        self.reference_tab = ReferenceTab()
        self.tab_view.append(self.reference_tab).set_title("Reference")

        self.community_tab = CommunityTab()
        self.tab_view.append(self.community_tab).set_title("Community")

        self.cheatsheet_tab = CheatsheetTab(self.config_manager)
        self.tab_view.append(self.cheatsheet_tab).set_title("Cheatsheet")

        # Load config asynchronously
        self._load_config_async()

    def _load_config_async(self) -> None:
        """Load config in background thread."""
        self._show_loading()

        def load_thread():
            self.config_manager.load()
            GLib.idle_add(self._on_config_loaded)

        thread = threading.Thread(target=load_thread, daemon=True)
        thread.start()

    def _on_config_loaded(self) -> None:
        """Config loaded - update tabs."""
        self._hide_loading()
        # Observers will auto-update tabs

    def _show_loading(self) -> None:
        self.loading_spinner.set_spinning(True)
        self.loading_spinner.set_visible(True)

    def _hide_loading(self) -> None:
        self.loading_spinner.set_spinning(False)
        self.loading_spinner.set_visible(False)

    def do_close_request(self) -> bool:
        """Handle close - check for unsaved changes."""
        if self.config_manager.is_dirty():
            dialog = Adw.MessageDialog.new(self)
            dialog.set_heading("Unsaved Changes")
            dialog.set_body("Save changes before closing?")
            dialog.add_response("discard", "Discard")
            dialog.add_response("cancel", "Cancel")
            dialog.add_response("save", "Save")
            dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)
            dialog.set_response_appearance("discard", Adw.ResponseAppearance.DESTRUCTIVE)
            dialog.connect("response", self._on_close_response)
            dialog.present()
            return True  # Block close

        return False  # Allow close

    def _on_close_response(self, dialog: Adw.MessageDialog, response: str) -> None:
        if response == "save":
            self.config_manager.save()
            self.close()
        elif response == "discard":
            self.close()
```

**Tests** (`tests/ui/test_main_window.py`):
```python
# Use direct references - NO tree traversal
def test_window_has_tab_view(app):
    window = MainWindow(application=app)
    assert window.tab_view is not None
    assert isinstance(window.tab_view, Adw.TabView)

def test_window_has_four_tabs(app):
    window = MainWindow(application=app)
    # Direct access
    assert window.tab_view.get_n_pages() == 4

def test_config_manager_initialized(app):
    window = MainWindow(application=app)
    assert window.config_manager is not None

def test_tabs_stored_as_attributes(app):
    window = MainWindow(application=app)
    assert window.editor_tab is not None
    assert window.reference_tab is not None
    assert window.community_tab is not None
    assert window.cheatsheet_tab is not None
```

---

See original plan for full context. Key additions: async, observers, dirty tracking, close handling.
