# HyprBind Implementation Plan - Phases 5-7
**Date**: 2025-11-12
**Author**: Planning Session after Foundation Polish
**Status**: Ready for Execution

---

## Overview

This plan details the implementation of the complete user interface and advanced features for HyprBind. The foundation (data models, parsers, logic layer, app shell) is complete with 51 passing tests and 84% coverage.

**What We're Building:**
- **Phase 5**: Complete 4-tab UI (Editor, Reference, Community, Cheatsheet)
- **Phase 6**: Backend integrations (file writer, backup, GitHub, exports)
- **Phase 7**: Advanced features (Hyprland IPC, Safe/Live modes, Wallust theming)

**Execution Strategy:**
- Continue TDD methodology (test → fail → implement → pass → commit)
- Identify parallel tasks and batch them
- Code review after each phase
- Target 90%+ coverage on new modules

---

## Phase 5: Core User Interface (Tasks 9-14)

### Task 9: Tab Navigation Structure
**Goal**: Implement AdwTabView with 4 tabs and navigation

**Dependencies**: None (uses existing main_window.py)

**Files to Create:**
- `data/ui/main_window.ui` (modify existing)
- `src/hyprbind/ui/editor_tab.py` (new)
- `src/hyprbind/ui/reference_tab.py` (new)
- `src/hyprbind/ui/community_tab.py` (new)
- `src/hyprbind/ui/cheatsheet_tab.py` (new)
- `tests/ui/test_main_window.py` (new)

**TDD Steps:**

1. **Write test** - `tests/ui/test_main_window.py`:
```python
"""Tests for main window with tabs."""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw
from hyprbind.ui.main_window import MainWindow
import pytest


@pytest.fixture
def app():
    """Create test application."""
    return Adw.Application(application_id="com.hyprbind.test")


def test_window_has_tab_view(app):
    """Main window contains AdwTabView."""
    window = MainWindow(application=app)

    # Find tab view in widget tree
    tab_view = None
    def find_tab_view(widget):
        nonlocal tab_view
        if isinstance(widget, Adw.TabView):
            tab_view = widget
            return
        if hasattr(widget, 'get_first_child'):
            child = widget.get_first_child()
            while child:
                find_tab_view(child)
                child = child.get_next_sibling()

    find_tab_view(window)
    assert tab_view is not None


def test_window_has_four_tabs(app):
    """Main window has Editor, Reference, Community, Cheatsheet tabs."""
    window = MainWindow(application=app)

    # Get tab view
    tab_view = window.tab_view

    # Should have 4 pages
    assert tab_view.get_n_pages() == 4

    # Check tab titles
    titles = []
    for i in range(4):
        page = tab_view.get_nth_page(i)
        titles.append(tab_view.get_page_title(page))

    assert "Editor" in titles
    assert "Reference" in titles
    assert "Community" in titles
    assert "Cheatsheet" in titles
```

2. **Verify test fails**: `pytest tests/ui/test_main_window.py -v`

3. **Create tab placeholder widgets**:

`src/hyprbind/ui/editor_tab.py`:
```python
"""Editor tab for managing keybindings."""

import gi
gi.require_version("Gtk", "4.0")

from gi.repository import Gtk


class EditorTab(Gtk.Box):
    """Tab for editing keybindings."""

    def __init__(self) -> None:
        """Initialize editor tab."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        # Placeholder label
        label = Gtk.Label(label="Editor Tab - Coming Soon")
        label.set_margin_top(50)
        label.set_margin_bottom(50)
        self.append(label)
```

`src/hyprbind/ui/reference_tab.py`:
```python
"""Reference tab for Hyprland keybinding documentation."""

import gi
gi.require_version("Gtk", "4.0")

from gi.repository import Gtk


class ReferenceTab(Gtk.Box):
    """Tab for Hyprland keybinding reference."""

    def __init__(self) -> None:
        """Initialize reference tab."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        # Placeholder label
        label = Gtk.Label(label="Reference Tab - Coming Soon")
        label.set_margin_top(50)
        label.set_margin_bottom(50)
        self.append(label)
```

`src/hyprbind/ui/community_tab.py`:
```python
"""Community tab for importing configs from GitHub."""

import gi
gi.require_version("Gtk", "4.0")

from gi.repository import Gtk


class CommunityTab(Gtk.Box):
    """Tab for community config imports."""

    def __init__(self) -> None:
        """Initialize community tab."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        # Placeholder label
        label = Gtk.Label(label="Community Tab - Coming Soon")
        label.set_margin_top(50)
        label.set_margin_bottom(50)
        self.append(label)
```

`src/hyprbind/ui/cheatsheet_tab.py`:
```python
"""Cheatsheet tab for viewing and exporting keybindings."""

import gi
gi.require_version("Gtk", "4.0")

from gi.repository import Gtk


class CheatsheetTab(Gtk.Box):
    """Tab for cheatsheet view and export."""

    def __init__(self) -> None:
        """Initialize cheatsheet tab."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        # Placeholder label
        label = Gtk.Label(label="Cheatsheet Tab - Coming Soon")
        label.set_margin_top(50)
        label.set_margin_bottom(50)
        self.append(label)
```

4. **Modify main_window.py** to add tab view:
```python
"""Main application window."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw
from pathlib import Path
from typing import Any
import sys

from hyprbind.ui.editor_tab import EditorTab
from hyprbind.ui.reference_tab import ReferenceTab
from hyprbind.ui.community_tab import CommunityTab
from hyprbind.ui.cheatsheet_tab import CheatsheetTab


def _get_ui_file_path() -> Path:
    # ... (existing implementation)


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
    tab_view: Adw.TabView = Gtk.Template.Child()

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the main window."""
        super().__init__(**kwargs)
        self._setup_tabs()

    def _setup_tabs(self) -> None:
        """Create and add all tabs."""
        # Editor tab
        editor = EditorTab()
        self.tab_view.append(editor).set_title("Editor")

        # Reference tab
        reference = ReferenceTab()
        self.tab_view.append(reference).set_title("Reference")

        # Community tab
        community = CommunityTab()
        self.tab_view.append(community).set_title("Community")

        # Cheatsheet tab
        cheatsheet = CheatsheetTab()
        self.tab_view.append(cheatsheet).set_title("Cheatsheet")
```

5. **Update UI template** - `data/ui/main_window.ui`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<interface>
  <requires lib="gtk" version="4.0"/>
  <requires lib="libadwaita" version="1.0"/>

  <template class="HyprBindMainWindow" parent="AdwApplicationWindow">
    <property name="title">HyprBind</property>
    <property name="default-width">1200</property>
    <property name="default-height">800</property>

    <child>
      <object class="GtkBox" id="main_content">
        <property name="orientation">vertical</property>

        <child>
          <object class="AdwHeaderBar" id="header_bar">
            <child type="end">
              <object class="GtkMenuButton">
                <property name="icon-name">open-menu-symbolic</property>
                <property name="tooltip-text">Main Menu</property>
              </object>
            </child>
          </object>
        </child>

        <child>
          <object class="AdwTabView" id="tab_view">
            <property name="vexpand">true</property>
          </object>
        </child>
      </object>
    </child>
  </template>
</interface>
```

6. **Verify tests pass**: `pytest tests/ui/test_main_window.py -v`

7. **Manual verification**:
```bash
cd /home/komi/repos/hyprbind/worktrees/dev
.venv/bin/python -m hyprbind
# Should see 4 tabs: Editor, Reference, Community, Cheatsheet
```

8. **Commit**:
```bash
git add src/hyprbind/ui/*.py data/ui/main_window.ui tests/ui/test_main_window.py
git commit -m "feat: Add tab navigation structure

Implement AdwTabView with 4 placeholder tabs:
- Editor tab for keybinding management
- Reference tab for Hyprland documentation
- Community tab for GitHub config imports
- Cheatsheet tab for visual display and export

All tabs have placeholder widgets. Ready for content implementation.

Tests: 2 new UI tests
Coverage: Tab structure and initialization

🤖 Generated with Claude Code
https://claude.com/claude-code"
```

---

### Task 10: Editor Tab - Binding List UI
**Goal**: Display all keybindings in a scrollable TreeView with categories

**Dependencies**: Task 9 (tab structure)

**Files to Modify:**
- `src/hyprbind/ui/editor_tab.py`
- `tests/ui/test_editor_tab.py` (new)

**TDD Steps:**

1. **Write test** - `tests/ui/test_editor_tab.py`:
```python
"""Tests for editor tab."""

import gi
gi.require_version("Gtk", "4.0")

from gi.repository import Gtk, Gio
import pytest
from pathlib import Path

from hyprbind.ui.editor_tab import EditorTab
from hyprbind.core.config_manager import ConfigManager


@pytest.fixture
def sample_config_path():
    """Path to sample keybinds config."""
    return Path(__file__).parent.parent / "fixtures" / "sample_keybinds.conf"


@pytest.fixture
def manager(sample_config_path):
    """ConfigManager with loaded config."""
    mgr = ConfigManager(sample_config_path)
    mgr.load()
    return mgr


def test_editor_tab_has_list_view(manager):
    """Editor tab contains a ListView for bindings."""
    tab = EditorTab(manager)

    # Find ListView in widget tree
    list_view = None
    def find_list_view(widget):
        nonlocal list_view
        if isinstance(widget, Gtk.ListView):
            list_view = widget
            return
        if hasattr(widget, 'get_first_child'):
            child = widget.get_first_child()
            while child:
                find_list_view(child)
                child = child.get_next_sibling()

    find_list_view(tab)
    assert list_view is not None


def test_editor_tab_displays_bindings(manager):
    """Editor tab displays all loaded bindings."""
    tab = EditorTab(manager)

    # Get the model
    list_view = tab.list_view
    model = list_view.get_model()

    # Should have items (number of bindings)
    bindings_count = len(manager.config.get_all_bindings())
    assert model.get_n_items() > 0
    assert model.get_n_items() == bindings_count


def test_editor_tab_shows_binding_details(manager):
    """Editor tab shows binding details (key, description, action)."""
    tab = EditorTab(manager)

    # Get first binding from model
    model = tab.list_view.get_model()
    first_item = model.get_item(0)

    # Item should have binding attributes
    binding = first_item.binding
    assert binding.key is not None
    assert binding.description is not None
    assert binding.action is not None
```

2. **Verify test fails**: `pytest tests/ui/test_editor_tab.py -v`

3. **Implement EditorTab**:

`src/hyprbind/ui/editor_tab.py`:
```python
"""Editor tab for managing keybindings."""

import gi
gi.require_version("Gtk", "4.0")

from gi.repository import Gtk, Gio, GObject
from typing import Optional

from hyprbind.core.config_manager import ConfigManager
from hyprbind.core.models import Binding


class BindingObject(GObject.Object):
    """Wrapper for Binding to use in Gio.ListStore."""

    binding: Binding = GObject.Property(type=object)

    def __init__(self, binding: Binding) -> None:
        """Initialize with binding."""
        super().__init__()
        self.binding = binding


class EditorTab(Gtk.Box):
    """Tab for editing keybindings."""

    def __init__(self, config_manager: ConfigManager) -> None:
        """Initialize editor tab with config manager."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        self.config_manager = config_manager

        # Create list store for bindings
        self.list_store = Gio.ListStore.new(BindingObject)

        # Create selection model
        self.selection_model = Gtk.SingleSelection.new(self.list_store)

        # Create list view
        self.list_view = Gtk.ListView.new(self.selection_model, None)

        # Create factory for list items
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._on_factory_setup)
        factory.connect("bind", self._on_factory_bind)
        self.list_view.set_factory(factory)

        # Add to scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_child(self.list_view)
        self.append(scrolled)

        # Toolbar
        toolbar = self._create_toolbar()
        self.prepend(toolbar)

        # Load bindings
        self._load_bindings()

    def _create_toolbar(self) -> Gtk.Box:
        """Create toolbar with add/edit/delete buttons."""
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        toolbar.add_css_class("toolbar")
        toolbar.set_margin_start(6)
        toolbar.set_margin_end(6)
        toolbar.set_margin_top(6)
        toolbar.set_margin_bottom(6)

        # Add button
        add_btn = Gtk.Button(label="Add", icon_name="list-add-symbolic")
        add_btn.set_tooltip_text("Add new binding")
        toolbar.append(add_btn)

        # Edit button
        edit_btn = Gtk.Button(label="Edit", icon_name="document-edit-symbolic")
        edit_btn.set_tooltip_text("Edit selected binding")
        toolbar.append(edit_btn)

        # Delete button
        delete_btn = Gtk.Button(label="Delete", icon_name="edit-delete-symbolic")
        delete_btn.set_tooltip_text("Delete selected binding")
        toolbar.append(delete_btn)

        return toolbar

    def _on_factory_setup(self, factory: Gtk.SignalListItemFactory,
                          list_item: Gtk.ListItem) -> None:
        """Setup list item widget."""
        # Create a box with labels for binding info
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(6)
        box.set_margin_bottom(6)

        # Key label
        key_label = Gtk.Label()
        key_label.set_name("key_label")
        key_label.set_width_chars(20)
        key_label.set_xalign(0)
        box.append(key_label)

        # Description label
        desc_label = Gtk.Label()
        desc_label.set_name("desc_label")
        desc_label.set_hexpand(True)
        desc_label.set_xalign(0)
        box.append(desc_label)

        # Action label
        action_label = Gtk.Label()
        action_label.set_name("action_label")
        action_label.set_width_chars(30)
        action_label.set_xalign(0)
        action_label.add_css_class("dim-label")
        box.append(action_label)

        list_item.set_child(box)

    def _on_factory_bind(self, factory: Gtk.SignalListItemFactory,
                        list_item: Gtk.ListItem) -> None:
        """Bind binding data to list item."""
        binding_obj = list_item.get_item()
        binding = binding_obj.binding

        box = list_item.get_child()

        # Find labels by name
        key_label = None
        desc_label = None
        action_label = None

        child = box.get_first_child()
        while child:
            if child.get_name() == "key_label":
                key_label = child
            elif child.get_name() == "desc_label":
                desc_label = child
            elif child.get_name() == "action_label":
                action_label = child
            child = child.get_next_sibling()

        # Set text
        if key_label:
            mods = " + ".join(binding.modifiers) if binding.modifiers else ""
            key_text = f"{mods} + {binding.key}" if mods else binding.key
            key_label.set_text(key_text)

        if desc_label:
            desc_label.set_text(binding.description or "No description")

        if action_label:
            action_text = f"{binding.action}"
            if binding.params:
                action_text += f", {binding.params}"
            action_label.set_text(action_text)

    def _load_bindings(self) -> None:
        """Load bindings from config manager into list."""
        if not self.config_manager.config:
            return

        bindings = self.config_manager.config.get_all_bindings()
        for binding in bindings:
            self.list_store.append(BindingObject(binding))
```

4. **Verify tests pass**: `pytest tests/ui/test_editor_tab.py -v`

5. **Update main_window.py** to pass config_manager:
```python
def _setup_tabs(self) -> None:
    """Create and add all tabs."""
    # Create config manager (use default path for now)
    from hyprbind.core.config_manager import ConfigManager
    self.config_manager = ConfigManager()
    self.config_manager.load()

    # Editor tab
    editor = EditorTab(self.config_manager)
    self.tab_view.append(editor).set_title("Editor")

    # ... (rest unchanged)
```

6. **Manual verification**:
```bash
cd /home/komi/repos/hyprbind/worktrees/dev
.venv/bin/python -m hyprbind
# Should see list of bindings in Editor tab
```

7. **Commit**:
```bash
git add src/hyprbind/ui/editor_tab.py tests/ui/test_editor_tab.py src/hyprbind/ui/main_window.py
git commit -m "feat: Implement binding list view in Editor tab

Add scrollable ListView displaying all keybindings with:
- Modifier + Key combination
- Description
- Action and parameters
- Toolbar with Add/Edit/Delete buttons (not yet functional)

Uses GObject wrapper for Binding to work with Gio.ListStore.

Tests: 3 new tests for list view
Coverage: EditorTab list display logic

🤖 Generated with Claude Code
https://claude.com/claude-code"
```

---

### Task 11: Editor Tab - CRUD Dialogs
**Goal**: Implement Add/Edit/Delete functionality with conflict detection UI

**Dependencies**: Task 10 (binding list)

**Files to Modify:**
- `src/hyprbind/ui/editor_tab.py`
- `src/hyprbind/ui/binding_dialog.py` (new)
- `tests/ui/test_binding_dialog.py` (new)

**TDD Steps:**

1. **Write test** - `tests/ui/test_binding_dialog.py`:
```python
"""Tests for binding edit dialog."""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw
import pytest

from hyprbind.ui.binding_dialog import BindingDialog
from hyprbind.core.models import Binding, BindType


def test_dialog_has_required_fields():
    """Dialog has fields for key, description, action, params."""
    dialog = BindingDialog()

    # Should have entry fields
    assert dialog.key_entry is not None
    assert dialog.description_entry is not None
    assert dialog.action_entry is not None
    assert dialog.params_entry is not None


def test_dialog_can_load_binding():
    """Dialog loads existing binding data."""
    binding = Binding(
        type=BindType.BINDD,
        modifiers=["$mainMod"],
        key="Q",
        description="Close window",
        action="killactive",
        params="",
        submap=None,
        line_number=10,
        category="Windows",
    )

    dialog = BindingDialog(binding=binding)

    assert dialog.key_entry.get_text() == "Q"
    assert dialog.description_entry.get_text() == "Close window"
    assert dialog.action_entry.get_text() == "killactive"


def test_dialog_get_binding_returns_new_binding():
    """Dialog can return constructed binding from fields."""
    dialog = BindingDialog()

    dialog.key_entry.set_text("T")
    dialog.description_entry.set_text("Test binding")
    dialog.action_entry.set_text("exec")
    dialog.params_entry.set_text("alacritty")

    binding = dialog.get_binding()

    assert binding.key == "T"
    assert binding.description == "Test binding"
    assert binding.action == "exec"
    assert binding.params == "alacritty"
```

2. **Verify test fails**: `pytest tests/ui/test_binding_dialog.py -v`

3. **Implement BindingDialog**:

`src/hyprbind/ui/binding_dialog.py`:
```python
"""Dialog for adding/editing keybindings."""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw
from typing import Optional

from hyprbind.core.models import Binding, BindType


class BindingDialog(Adw.Window):
    """Dialog for creating or editing a keybinding."""

    def __init__(self, binding: Optional[Binding] = None,
                 parent: Optional[Gtk.Window] = None) -> None:
        """Initialize binding dialog.

        Args:
            binding: Existing binding to edit (None for new binding)
            parent: Parent window
        """
        super().__init__()

        self.binding = binding
        self.set_title("Edit Binding" if binding else "Add Binding")
        self.set_default_size(500, 400)
        self.set_modal(True)

        if parent:
            self.set_transient_for(parent)

        self._create_ui()

        if binding:
            self._load_binding(binding)

    def _create_ui(self) -> None:
        """Create dialog UI."""
        # Main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # Header bar
        header = Adw.HeaderBar()
        main_box.append(header)

        # Content area with form
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_start(24)
        content.set_margin_end(24)
        content.set_margin_top(24)
        content.set_margin_bottom(24)

        # Key entry
        key_group = Adw.PreferencesGroup()
        key_row = Adw.EntryRow()
        key_row.set_title("Key")
        key_row.set_text("")
        self.key_entry = key_row
        key_group.add(key_row)
        content.append(key_group)

        # Modifiers entry
        mod_group = Adw.PreferencesGroup()
        mod_row = Adw.EntryRow()
        mod_row.set_title("Modifiers")
        mod_row.set_text("$mainMod")
        self.modifiers_entry = mod_row
        content.append(mod_group)

        # Description entry
        desc_group = Adw.PreferencesGroup()
        desc_row = Adw.EntryRow()
        desc_row.set_title("Description")
        desc_row.set_text("")
        self.description_entry = desc_row
        desc_group.add(desc_row)
        content.append(desc_group)

        # Action entry
        action_group = Adw.PreferencesGroup()
        action_row = Adw.EntryRow()
        action_row.set_title("Action")
        action_row.set_text("exec")
        self.action_entry = action_row
        action_group.add(action_row)
        content.append(action_group)

        # Params entry
        params_group = Adw.PreferencesGroup()
        params_row = Adw.EntryRow()
        params_row.set_title("Parameters")
        params_row.set_text("")
        self.params_entry = params_row
        params_group.add(params_row)
        content.append(params_group)

        # Action buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(12)

        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect("clicked", lambda _: self.close())
        button_box.append(cancel_btn)

        save_btn = Gtk.Button(label="Save")
        save_btn.add_css_class("suggested-action")
        save_btn.connect("clicked", self._on_save_clicked)
        button_box.append(save_btn)

        content.append(button_box)

        main_box.append(content)
        self.set_content(main_box)

    def _load_binding(self, binding: Binding) -> None:
        """Load binding data into form."""
        self.key_entry.set_text(binding.key)

        if binding.modifiers:
            self.modifiers_entry.set_text(", ".join(binding.modifiers))

        if binding.description:
            self.description_entry.set_text(binding.description)

        if binding.action:
            self.action_entry.set_text(binding.action)

        if binding.params:
            self.params_entry.set_text(binding.params)

    def _on_save_clicked(self, button: Gtk.Button) -> None:
        """Handle save button click."""
        # Will be implemented in next iteration
        self.close()

    def get_binding(self) -> Binding:
        """Construct binding from form data."""
        # Parse modifiers
        mod_text = self.modifiers_entry.get_text()
        modifiers = [m.strip() for m in mod_text.split(",") if m.strip()]

        return Binding(
            type=BindType.BINDD,
            modifiers=modifiers,
            key=self.key_entry.get_text(),
            description=self.description_entry.get_text(),
            action=self.action_entry.get_text(),
            params=self.params_entry.get_text(),
            submap=None,
            line_number=0,
            category="Custom",
        )
```

4. **Wire up dialog in EditorTab**:

Modify `src/hyprbind/ui/editor_tab.py`:
```python
# In _create_toolbar():
add_btn.connect("clicked", self._on_add_clicked)
edit_btn.connect("clicked", self._on_edit_clicked)
delete_btn.connect("clicked", self._on_delete_clicked)

# Add methods:
def _on_add_clicked(self, button: Gtk.Button) -> None:
    """Handle add button click."""
    from hyprbind.ui.binding_dialog import BindingDialog

    dialog = BindingDialog(parent=self.get_root())
    dialog.connect("close-request", self._on_dialog_closed)
    dialog.present()

def _on_edit_clicked(self, button: Gtk.Button) -> None:
    """Handle edit button click."""
    # Get selected binding
    position = self.selection_model.get_selected()
    if position == Gtk.INVALID_LIST_POSITION:
        return

    binding_obj = self.selection_model.get_selected_item()
    binding = binding_obj.binding

    from hyprbind.ui.binding_dialog import BindingDialog

    dialog = BindingDialog(binding=binding, parent=self.get_root())
    dialog.connect("close-request", self._on_dialog_closed)
    dialog.present()

def _on_delete_clicked(self, button: Gtk.Button) -> None:
    """Handle delete button click."""
    # Get selected binding
    position = self.selection_model.get_selected()
    if position == Gtk.INVALID_LIST_POSITION:
        return

    binding_obj = self.selection_model.get_selected_item()
    binding = binding_obj.binding

    # Show confirmation dialog
    dialog = Adw.MessageDialog.new(self.get_root())
    dialog.set_heading("Delete Binding?")
    dialog.set_body(f"Delete binding: {binding.description}?")
    dialog.add_response("cancel", "Cancel")
    dialog.add_response("delete", "Delete")
    dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
    dialog.connect("response", self._on_delete_response, binding, position)
    dialog.present()

def _on_delete_response(self, dialog: Adw.MessageDialog, response: str,
                       binding: Binding, position: int) -> None:
    """Handle delete confirmation response."""
    if response == "delete":
        result = self.config_manager.remove_binding(binding)
        if result.success:
            self.list_store.remove(position)

def _on_dialog_closed(self, dialog: Adw.Window) -> None:
    """Handle dialog close - reload bindings if needed."""
    # Will implement save logic in next iteration
    pass
```

5. **Verify tests pass**: `pytest tests/ui/test_binding_dialog.py tests/ui/test_editor_tab.py -v`

6. **Manual verification**:
```bash
cd /home/komi/repos/hyprbind/worktrees/dev
.venv/bin/python -m hyprbind
# Click Add/Edit/Delete buttons - dialogs should open
```

7. **Commit**:
```bash
git add src/hyprbind/ui/binding_dialog.py tests/ui/test_binding_dialog.py src/hyprbind/ui/editor_tab.py
git commit -m "feat: Add binding CRUD dialogs

Implement add/edit/delete functionality:
- BindingDialog with form fields (key, modifiers, description, action, params)
- Add button opens empty dialog
- Edit button loads selected binding
- Delete button shows confirmation dialog
- Integrates with ConfigManager for operations

Note: Save logic will be implemented in next iteration with conflict detection UI.

Tests: 3 new tests for dialog
Coverage: Dialog creation and data loading

🤖 Generated with Claude Code
https://claude.com/claude-code"
```

---

### Task 12: Reference Tab - Hyprland Documentation
**Goal**: Display searchable Hyprland keybinding reference

**Dependencies**: None (independent)

**Files to Modify:**
- `src/hyprbind/ui/reference_tab.py`
- `src/hyprbind/data/hyprland_reference.py` (new)
- `tests/ui/test_reference_tab.py` (new)
- `tests/data/test_hyprland_reference.py` (new)

**TDD Steps:**

1. **Write test** - `tests/data/test_hyprland_reference.py`:
```python
"""Tests for Hyprland reference data."""

from hyprbind.data.hyprland_reference import HYPRLAND_ACTIONS


def test_reference_data_exists():
    """Reference data is available."""
    assert len(HYPRLAND_ACTIONS) > 0


def test_reference_data_structure():
    """Reference data has correct structure."""
    action = HYPRLAND_ACTIONS[0]

    assert "name" in action
    assert "description" in action
    assert "example" in action


def test_reference_includes_common_actions():
    """Reference includes common Hyprland actions."""
    action_names = [a["name"] for a in HYPRLAND_ACTIONS]

    assert "killactive" in action_names
    assert "exec" in action_names
    assert "workspace" in action_names
    assert "movetoworkspace" in action_names
```

2. **Verify test fails**: `pytest tests/data/test_hyprland_reference.py -v`

3. **Create reference data**:

`src/hyprbind/data/__init__.py`:
```python
"""Data module for reference information."""
```

`src/hyprbind/data/hyprland_reference.py`:
```python
"""Hyprland keybinding action reference data."""

HYPRLAND_ACTIONS = [
    {
        "name": "exec",
        "description": "Execute a shell command",
        "example": "exec, alacritty",
    },
    {
        "name": "killactive",
        "description": "Close the active window",
        "example": "killactive,",
    },
    {
        "name": "workspace",
        "description": "Switch to a workspace",
        "example": "workspace, 1",
    },
    {
        "name": "movetoworkspace",
        "description": "Move active window to workspace",
        "example": "movetoworkspace, 2",
    },
    {
        "name": "togglefloating",
        "description": "Toggle floating mode for active window",
        "example": "togglefloating,",
    },
    {
        "name": "fullscreen",
        "description": "Toggle fullscreen for active window",
        "example": "fullscreen, 0",
    },
    {
        "name": "movefocus",
        "description": "Move focus in direction",
        "example": "movefocus, l",
    },
    {
        "name": "movewindow",
        "description": "Move window in direction",
        "example": "movewindow, r",
    },
    {
        "name": "resizeactive",
        "description": "Resize active window",
        "example": "resizeactive, 20 0",
    },
    {
        "name": "cyclenext",
        "description": "Focus next window",
        "example": "cyclenext,",
    },
    {
        "name": "swapnext",
        "description": "Swap with next window",
        "example": "swapnext,",
    },
    {
        "name": "exit",
        "description": "Exit Hyprland",
        "example": "exit,",
    },
    {
        "name": "forcerendererreload",
        "description": "Force renderer reload",
        "example": "forcerendererreload,",
    },
    {
        "name": "togglegroup",
        "description": "Toggle window grouping",
        "example": "togglegroup,",
    },
    {
        "name": "changegroupactive",
        "description": "Change active window in group",
        "example": "changegroupactive, f",
    },
    {
        "name": "togglesplit",
        "description": "Toggle split direction",
        "example": "togglesplit,",
    },
    {
        "name": "layoutmsg",
        "description": "Send message to layout",
        "example": "layoutmsg, preselect l",
    },
    {
        "name": "pin",
        "description": "Pin active window",
        "example": "pin,",
    },
]
```

4. **Write test for UI** - `tests/ui/test_reference_tab.py`:
```python
"""Tests for reference tab."""

import gi
gi.require_version("Gtk", "4.0")

from gi.repository import Gtk
import pytest

from hyprbind.ui.reference_tab import ReferenceTab


def test_reference_tab_has_list_view():
    """Reference tab contains ListView for actions."""
    tab = ReferenceTab()

    # Find ListView
    list_view = None
    def find_list_view(widget):
        nonlocal list_view
        if isinstance(widget, Gtk.ListView):
            list_view = widget
            return
        if hasattr(widget, 'get_first_child'):
            child = widget.get_first_child()
            while child:
                find_list_view(child)
                child = child.get_next_sibling()

    find_list_view(tab)
    assert list_view is not None


def test_reference_tab_displays_actions():
    """Reference tab displays action reference data."""
    tab = ReferenceTab()

    model = tab.list_view.get_model()
    assert model.get_n_items() > 0
```

5. **Implement ReferenceTab**:

`src/hyprbind/ui/reference_tab.py`:
```python
"""Reference tab for Hyprland keybinding documentation."""

import gi
gi.require_version("Gtk", "4.0")

from gi.repository import Gtk, Gio, GObject

from hyprbind.data.hyprland_reference import HYPRLAND_ACTIONS


class ActionObject(GObject.Object):
    """Wrapper for action reference data."""

    action: dict = GObject.Property(type=object)

    def __init__(self, action: dict) -> None:
        """Initialize with action dict."""
        super().__init__()
        self.action = action


class ReferenceTab(Gtk.Box):
    """Tab for Hyprland keybinding reference."""

    def __init__(self) -> None:
        """Initialize reference tab."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        # Search bar
        search_entry = Gtk.SearchEntry()
        search_entry.set_placeholder_text("Search actions...")
        search_entry.set_margin_start(12)
        search_entry.set_margin_end(12)
        search_entry.set_margin_top(12)
        search_entry.set_margin_bottom(6)
        search_entry.connect("search-changed", self._on_search_changed)
        self.search_entry = search_entry
        self.append(search_entry)

        # Create list store
        self.list_store = Gio.ListStore.new(ActionObject)

        # Create filter model
        self.filter = Gtk.CustomFilter.new(self._filter_func, None)
        self.filter_model = Gtk.FilterListModel.new(self.list_store, self.filter)

        # Create selection model
        self.selection_model = Gtk.SingleSelection.new(self.filter_model)

        # Create list view
        self.list_view = Gtk.ListView.new(self.selection_model, None)

        # Create factory
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._on_factory_setup)
        factory.connect("bind", self._on_factory_bind)
        self.list_view.set_factory(factory)

        # Add to scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_child(self.list_view)
        self.append(scrolled)

        # Load actions
        self._load_actions()

    def _load_actions(self) -> None:
        """Load action reference data."""
        for action in HYPRLAND_ACTIONS:
            self.list_store.append(ActionObject(action))

    def _on_factory_setup(self, factory: Gtk.SignalListItemFactory,
                         list_item: Gtk.ListItem) -> None:
        """Setup list item widget."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(8)
        box.set_margin_bottom(8)

        # Action name
        name_label = Gtk.Label()
        name_label.set_name("name_label")
        name_label.set_xalign(0)
        name_label.add_css_class("heading")
        box.append(name_label)

        # Description
        desc_label = Gtk.Label()
        desc_label.set_name("desc_label")
        desc_label.set_xalign(0)
        desc_label.set_wrap(True)
        box.append(desc_label)

        # Example
        example_label = Gtk.Label()
        example_label.set_name("example_label")
        example_label.set_xalign(0)
        example_label.add_css_class("dim-label")
        example_label.add_css_class("monospace")
        box.append(example_label)

        list_item.set_child(box)

    def _on_factory_bind(self, factory: Gtk.SignalListItemFactory,
                        list_item: Gtk.ListItem) -> None:
        """Bind action data to list item."""
        action_obj = list_item.get_item()
        action = action_obj.action

        box = list_item.get_child()

        # Find labels
        name_label = None
        desc_label = None
        example_label = None

        child = box.get_first_child()
        while child:
            if child.get_name() == "name_label":
                name_label = child
            elif child.get_name() == "desc_label":
                desc_label = child
            elif child.get_name() == "example_label":
                example_label = child
            child = child.get_next_sibling()

        # Set text
        if name_label:
            name_label.set_text(action["name"])
        if desc_label:
            desc_label.set_text(action["description"])
        if example_label:
            example_label.set_text(f"Example: {action['example']}")

    def _filter_func(self, item: ActionObject, user_data) -> bool:
        """Filter function for search."""
        search_text = self.search_entry.get_text().lower()
        if not search_text:
            return True

        action = item.action
        return (
            search_text in action["name"].lower()
            or search_text in action["description"].lower()
        )

    def _on_search_changed(self, entry: Gtk.SearchEntry) -> None:
        """Handle search text change."""
        self.filter.changed(Gtk.FilterChange.DIFFERENT)
```

6. **Verify tests pass**:
```bash
pytest tests/data/test_hyprland_reference.py tests/ui/test_reference_tab.py -v
```

7. **Manual verification**:
```bash
cd /home/komi/repos/hyprbind/worktrees/dev
.venv/bin/python -m hyprbind
# Switch to Reference tab, should see list of actions
# Type in search box, list should filter
```

8. **Commit**:
```bash
git add src/hyprbind/data/ src/hyprbind/ui/reference_tab.py tests/
git commit -m "feat: Add Hyprland reference documentation tab

Implement reference tab with:
- Static data of common Hyprland actions
- Searchable/filterable list view
- Action name, description, and example for each entry

Reference data includes 18 common actions (exec, killactive, workspace, etc.).
Users can search by action name or description.

Tests: 4 new tests (data + UI)
Coverage: Reference data and tab display logic

🤖 Generated with Claude Code
https://claude.com/claude-code"
```

---

### Task 13: Community Tab - GitHub Config Importer
**Goal**: Fetch and import Hyprland configs from GitHub URLs

**Dependencies**: None (independent)

**Note**: This will be a placeholder for now. Full implementation requires Firecrawl MCP integration which is Phase 6 work.

**Files to Modify:**
- `src/hyprbind/ui/community_tab.py`
- `tests/ui/test_community_tab.py` (new)

**TDD Steps:**

1. **Write test** - `tests/ui/test_community_tab.py`:
```python
"""Tests for community tab."""

import gi
gi.require_version("Gtk", "4.0")

from gi.repository import Gtk
import pytest

from hyprbind.ui.community_tab import CommunityTab


def test_community_tab_has_url_entry():
    """Community tab has URL input field."""
    tab = CommunityTab()

    assert tab.url_entry is not None


def test_community_tab_has_fetch_button():
    """Community tab has fetch button."""
    tab = CommunityTab()

    # Find button in widget tree
    button = None
    def find_button(widget):
        nonlocal button
        if isinstance(widget, Gtk.Button):
            button = widget
            return
        if hasattr(widget, 'get_first_child'):
            child = widget.get_first_child()
            while child:
                find_button(child)
                child = child.get_next_sibling()

    find_button(tab)
    assert button is not None
```

2. **Verify test fails**: `pytest tests/ui/test_community_tab.py -v`

3. **Implement CommunityTab**:

`src/hyprbind/ui/community_tab.py`:
```python
"""Community tab for importing configs from GitHub."""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw


class CommunityTab(Gtk.Box):
    """Tab for community config imports."""

    def __init__(self) -> None:
        """Initialize community tab."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        # Info banner
        banner = Adw.Banner()
        banner.set_title("GitHub Config Importer")
        banner.set_button_label("Learn More")
        banner.set_revealed(True)
        self.append(banner)

        # Content
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_start(24)
        content.set_margin_end(24)
        content.set_margin_top(24)
        content.set_valign(Gtk.Align.START)

        # URL entry
        url_group = Adw.PreferencesGroup()
        url_group.set_title("GitHub Repository")
        url_group.set_description("Enter a GitHub repository URL to import Hyprland configs")

        self.url_entry = Adw.EntryRow()
        self.url_entry.set_title("Repository URL")
        self.url_entry.set_text("https://github.com/username/dotfiles")
        url_group.add(self.url_entry)

        content.append(url_group)

        # Fetch button
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_halign(Gtk.Align.START)
        button_box.set_margin_top(12)

        fetch_btn = Gtk.Button(label="Fetch Configs")
        fetch_btn.add_css_class("suggested-action")
        fetch_btn.connect("clicked", self._on_fetch_clicked)
        button_box.append(fetch_btn)

        content.append(button_box)

        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_xalign(0)
        self.status_label.set_margin_top(12)
        self.status_label.add_css_class("dim-label")
        content.append(self.status_label)

        self.append(content)

    def _on_fetch_clicked(self, button: Gtk.Button) -> None:
        """Handle fetch button click."""
        url = self.url_entry.get_text()

        # Placeholder - will implement with Firecrawl MCP in Phase 6
        self.status_label.set_text(
            f"GitHub fetcher coming in Phase 6!\n"
            f"Will fetch: {url}"
        )
```

4. **Verify tests pass**: `pytest tests/ui/test_community_tab.py -v`

5. **Manual verification**:
```bash
cd /home/komi/repos/hyprbind/worktrees/dev
.venv/bin/python -m hyprbind
# Switch to Community tab, should see URL entry and fetch button
```

6. **Commit**:
```bash
git add src/hyprbind/ui/community_tab.py tests/ui/test_community_tab.py
git commit -m "feat: Add Community tab placeholder

Implement Community tab UI structure:
- GitHub repository URL input
- Fetch button
- Status display area
- Info banner

Actual GitHub fetching will be implemented in Phase 6 with Firecrawl MCP integration.

Tests: 2 new tests for tab structure
Coverage: Community tab UI layout

🤖 Generated with Claude Code
https://claude.com/claude-code"
```

---

### Task 14: Cheatsheet Tab - Visual Display and Export
**Goal**: Visual cheatsheet view with export buttons

**Dependencies**: None (independent)

**Files to Modify:**
- `src/hyprbind/ui/cheatsheet_tab.py`
- `tests/ui/test_cheatsheet_tab.py` (new)

**TDD Steps:**

1. **Write test** - `tests/ui/test_cheatsheet_tab.py`:
```python
"""Tests for cheatsheet tab."""

import gi
gi.require_version("Gtk", "4.0")

from gi.repository import Gtk
import pytest
from pathlib import Path

from hyprbind.ui.cheatsheet_tab import CheatsheetTab
from hyprbind.core.config_manager import ConfigManager


@pytest.fixture
def sample_config_path():
    """Path to sample keybinds config."""
    return Path(__file__).parent.parent / "fixtures" / "sample_keybinds.conf"


@pytest.fixture
def manager(sample_config_path):
    """ConfigManager with loaded config."""
    mgr = ConfigManager(sample_config_path)
    mgr.load()
    return mgr


def test_cheatsheet_tab_has_grid_view(manager):
    """Cheatsheet tab has grid view for bindings."""
    tab = CheatsheetTab(manager)

    # Find GridView
    grid_view = None
    def find_grid_view(widget):
        nonlocal grid_view
        if isinstance(widget, Gtk.GridView):
            grid_view = widget
            return
        if hasattr(widget, 'get_first_child'):
            child = widget.get_first_child()
            while child:
                find_grid_view(child)
                child = child.get_next_sibling()

    find_grid_view(tab)
    assert grid_view is not None


def test_cheatsheet_tab_has_export_buttons(manager):
    """Cheatsheet tab has export buttons."""
    tab = CheatsheetTab(manager)

    # Should have export buttons
    assert tab.export_pdf_btn is not None
    assert tab.export_html_btn is not None
    assert tab.export_md_btn is not None
```

2. **Verify test fails**: `pytest tests/ui/test_cheatsheet_tab.py -v`

3. **Implement CheatsheetTab**:

`src/hyprbind/ui/cheatsheet_tab.py`:
```python
"""Cheatsheet tab for viewing and exporting keybindings."""

import gi
gi.require_version("Gtk", "4.0")

from gi.repository import Gtk, Gio, GObject
from typing import Optional

from hyprbind.core.config_manager import ConfigManager
from hyprbind.core.models import Binding


class BindingCardObject(GObject.Object):
    """Wrapper for Binding for GridView."""

    binding: Binding = GObject.Property(type=object)

    def __init__(self, binding: Binding) -> None:
        """Initialize with binding."""
        super().__init__()
        self.binding = binding


class CheatsheetTab(Gtk.Box):
    """Tab for cheatsheet view and export."""

    def __init__(self, config_manager: ConfigManager) -> None:
        """Initialize cheatsheet tab."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        self.config_manager = config_manager

        # Toolbar with export buttons
        toolbar = self._create_toolbar()
        self.append(toolbar)

        # Create list store
        self.list_store = Gio.ListStore.new(BindingCardObject)

        # Create selection model
        self.selection_model = Gtk.SingleSelection.new(self.list_store)

        # Create grid view
        self.grid_view = Gtk.GridView.new(self.selection_model, None)
        self.grid_view.set_max_columns(3)
        self.grid_view.set_min_columns(1)

        # Create factory
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._on_factory_setup)
        factory.connect("bind", self._on_factory_bind)
        self.grid_view.set_factory(factory)

        # Add to scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_child(self.grid_view)
        self.append(scrolled)

        # Load bindings
        self._load_bindings()

    def _create_toolbar(self) -> Gtk.Box:
        """Create toolbar with export buttons."""
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        toolbar.set_margin_start(12)
        toolbar.set_margin_end(12)
        toolbar.set_margin_top(12)
        toolbar.set_margin_bottom(6)

        # Export label
        label = Gtk.Label(label="Export:")
        toolbar.append(label)

        # PDF button
        self.export_pdf_btn = Gtk.Button(label="PDF")
        self.export_pdf_btn.set_tooltip_text("Export to PDF")
        self.export_pdf_btn.connect("clicked", self._on_export_pdf)
        toolbar.append(self.export_pdf_btn)

        # HTML button
        self.export_html_btn = Gtk.Button(label="HTML")
        self.export_html_btn.set_tooltip_text("Export to HTML")
        self.export_html_btn.connect("clicked", self._on_export_html)
        toolbar.append(self.export_html_btn)

        # Markdown button
        self.export_md_btn = Gtk.Button(label="Markdown")
        self.export_md_btn.set_tooltip_text("Export to Markdown")
        self.export_md_btn.connect("clicked", self._on_export_markdown)
        toolbar.append(self.export_md_btn)

        return toolbar

    def _on_factory_setup(self, factory: Gtk.SignalListItemFactory,
                         list_item: Gtk.ListItem) -> None:
        """Setup list item widget - create card."""
        frame = Gtk.Frame()
        frame.set_margin_start(6)
        frame.set_margin_end(6)
        frame.set_margin_top(6)
        frame.set_margin_bottom(6)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card.set_margin_start(12)
        card.set_margin_end(12)
        card.set_margin_top(12)
        card.set_margin_bottom(12)

        # Key combination (large)
        key_label = Gtk.Label()
        key_label.set_name("key_label")
        key_label.add_css_class("title-2")
        key_label.set_wrap(True)
        key_label.set_xalign(0.5)
        card.append(key_label)

        # Description
        desc_label = Gtk.Label()
        desc_label.set_name("desc_label")
        desc_label.set_wrap(True)
        desc_label.set_xalign(0.5)
        desc_label.set_justify(Gtk.Justification.CENTER)
        card.append(desc_label)

        frame.set_child(card)
        list_item.set_child(frame)

    def _on_factory_bind(self, factory: Gtk.SignalListItemFactory,
                        list_item: Gtk.ListItem) -> None:
        """Bind binding data to card."""
        binding_obj = list_item.get_item()
        binding = binding_obj.binding

        frame = list_item.get_child()
        card = frame.get_child()

        # Find labels
        key_label = None
        desc_label = None

        child = card.get_first_child()
        while child:
            if child.get_name() == "key_label":
                key_label = child
            elif child.get_name() == "desc_label":
                desc_label = child
            child = child.get_next_sibling()

        # Set text
        if key_label:
            mods = " + ".join(binding.modifiers) if binding.modifiers else ""
            key_text = f"{mods} + {binding.key}" if mods else binding.key
            key_label.set_text(key_text)

        if desc_label:
            desc_label.set_text(binding.description or "No description")

    def _load_bindings(self) -> None:
        """Load bindings into grid."""
        if not self.config_manager.config:
            return

        bindings = self.config_manager.config.get_all_bindings()
        for binding in bindings:
            self.list_store.append(BindingCardObject(binding))

    def _on_export_pdf(self, button: Gtk.Button) -> None:
        """Handle PDF export."""
        # Placeholder - will implement in Phase 6
        print("PDF export - coming in Phase 6")

    def _on_export_html(self, button: Gtk.Button) -> None:
        """Handle HTML export."""
        # Placeholder - will implement in Phase 6
        print("HTML export - coming in Phase 6")

    def _on_export_markdown(self, button: Gtk.Button) -> None:
        """Handle Markdown export."""
        # Placeholder - will implement in Phase 6
        print("Markdown export - coming in Phase 6")
```

4. **Update main_window.py** to pass config_manager:
```python
# In _setup_tabs():
cheatsheet = CheatsheetTab(self.config_manager)
self.tab_view.append(cheatsheet).set_title("Cheatsheet")
```

5. **Verify tests pass**: `pytest tests/ui/test_cheatsheet_tab.py -v`

6. **Manual verification**:
```bash
cd /home/komi/repos/hyprbind/worktrees/dev
.venv/bin/python -m hyprbind
# Switch to Cheatsheet tab, should see grid of binding cards
```

7. **Commit**:
```bash
git add src/hyprbind/ui/cheatsheet_tab.py tests/ui/test_cheatsheet_tab.py src/hyprbind/ui/main_window.py
git commit -m "feat: Add Cheatsheet tab with visual grid display

Implement cheatsheet tab:
- GridView displaying bindings as cards
- Large key combination text
- Centered description
- Export buttons (PDF, HTML, Markdown) - placeholders

Visual cheatsheet provides at-a-glance view of all keybindings.
Export functionality will be implemented in Phase 6.

Tests: 2 new tests for grid view and export buttons
Coverage: Cheatsheet tab display logic

🤖 Generated with Claude Code
https://claude.com/claude-code"
```

---

## Phase 5 Complete - Batch Review

**After Task 14, run code review batch:**

Deploy 4 code-reviewer agents:
1. Editor Tab Review (Tasks 10-11)
2. Reference Tab Review (Task 12)
3. Community Tab Review (Task 13)
4. Cheatsheet Tab Review (Task 14)

**Then address any issues found before proceeding to Phase 6.**

---

## Phase 6: Backend Integrations (Tasks 15-19)

### Task 15: Config File Writer
**Goal**: Save modified config back to disk in correct format

**Dependencies**: Tasks 10-11 (binding CRUD)

**Files to Create:**
- `src/hyprbind/core/config_writer.py`
- `tests/core/test_config_writer.py`

**TDD Steps:**

1. **Write test** - `tests/core/test_config_writer.py`:
```python
"""Tests for ConfigWriter."""

import pytest
from pathlib import Path
import tempfile

from hyprbind.core.config_writer import ConfigWriter
from hyprbind.core.models import Config, Binding, BindType


@pytest.fixture
def sample_config():
    """Create sample config."""
    config = Config(file_path="test.conf", original_content="")

    # Add some bindings
    config.add_binding(Binding(
        type=BindType.BINDD,
        modifiers=["$mainMod"],
        key="Q",
        description="Close window",
        action="killactive",
        params="",
        submap=None,
        line_number=0,
        category="Window Actions",
    ))

    config.add_binding(Binding(
        type=BindType.BINDD,
        modifiers=["$mainMod"],
        key="T",
        description="Terminal",
        action="exec",
        params="alacritty",
        submap=None,
        line_number=0,
        category="Applications",
    ))

    return config


def test_write_config_to_file(sample_config):
    """Write config to file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.conf') as f:
        output_path = Path(f.name)

    try:
        ConfigWriter.write_file(sample_config, output_path)

        # File should exist
        assert output_path.exists()

        # Read back
        content = output_path.read_text()

        # Should contain bindings
        assert "bindd" in content
        assert "$mainMod" in content
        assert "Q" in content
        assert "Close window" in content
    finally:
        output_path.unlink()


def test_write_config_preserves_categories(sample_config):
    """Written config groups bindings by category."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.conf') as f:
        output_path = Path(f.name)

    try:
        ConfigWriter.write_file(sample_config, output_path)

        content = output_path.read_text()

        # Should have category headers
        assert "Window Actions" in content
        assert "Applications" in content
    finally:
        output_path.unlink()


def test_write_config_format(sample_config):
    """Written config follows correct format."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.conf') as f:
        output_path = Path(f.name)

    try:
        ConfigWriter.write_file(sample_config, output_path)

        content = output_path.read_text()

        # Check format: bindd = MOD, KEY, Description, action, params
        lines = content.split('\n')
        binding_lines = [l for l in lines if l.startswith('bindd')]

        assert len(binding_lines) == 2

        # First binding
        assert "bindd = $mainMod, Q, Close window, killactive," in binding_lines[0]
    finally:
        output_path.unlink()
```

2. **Verify test fails**: `pytest tests/core/test_config_writer.py -v`

3. **Implement ConfigWriter**:

`src/hyprbind/core/config_writer.py`:
```python
"""Config file writer for saving keybindings."""

from pathlib import Path
from typing import List

from hyprbind.core.models import Config, Binding


class ConfigWriter:
    """Writes Config objects to Hyprland config files."""

    @staticmethod
    def write_file(config: Config, output_path: Path) -> None:
        """Write config to file.

        Args:
            config: Config object to write
            output_path: Path to output file
        """
        lines = ConfigWriter.generate_content(config)
        output_path.write_text("\n".join(lines))

    @staticmethod
    def generate_content(config: Config) -> List[str]:
        """Generate config file content as list of lines.

        Args:
            config: Config object

        Returns:
            List of lines for config file
        """
        lines = []

        # Group bindings by category
        for category in sorted(config.categories.keys()):
            bindings = config.categories[category]

            if not bindings:
                continue

            # Category header
            lines.append("")
            lines.append(f"# ======= {category} =======")

            # Bindings in category
            for binding in bindings:
                line = ConfigWriter._format_binding(binding)
                lines.append(line)

        return lines

    @staticmethod
    def _format_binding(binding: Binding) -> str:
        """Format a binding as a config line.

        Args:
            binding: Binding to format

        Returns:
            Formatted config line
        """
        bind_type = binding.type.value

        # Modifiers
        mods = ", ".join(binding.modifiers) if binding.modifiers else ""

        # Build line based on type
        if binding.type.value == "bindd":
            # bindd = MODS, KEY, Description, action, params
            return f"{bind_type} = {mods}, {binding.key}, {binding.description}, {binding.action}, {binding.params or ''}"
        elif binding.type.value == "bind":
            # bind = MODS, KEY, action, params
            return f"{bind_type} = {mods}, {binding.key}, {binding.action}, {binding.params or ''}"
        else:
            # Other types (bindel, bindm, etc.)
            return f"{bind_type} = {mods}, {binding.key}, {binding.action}, {binding.params or ''}"
```

4. **Wire up save functionality in ConfigManager**:

Add to `src/hyprbind/core/config_manager.py`:
```python
from hyprbind.core.config_writer import ConfigWriter

# Add method:
def save(self, output_path: Optional[Path] = None) -> OperationResult:
    """Save config to file.

    Args:
        output_path: Path to save to (defaults to config_path)

    Returns:
        OperationResult with success status
    """
    if not self.config:
        return OperationResult(
            success=False,
            message="Config not loaded - nothing to save",
        )

    target_path = output_path or self.config_path

    try:
        ConfigWriter.write_file(self.config, target_path)
        return OperationResult(
            success=True,
            message=f"Config saved to {target_path}",
        )
    except Exception as e:
        return OperationResult(
            success=False,
            message=f"Failed to save config: {e}",
        )
```

5. **Wire up save in BindingDialog**:

Update `src/hyprbind/ui/binding_dialog.py`:
```python
# Add config_manager parameter:
def __init__(self, config_manager: ConfigManager,
             binding: Optional[Binding] = None,
             parent: Optional[Gtk.Window] = None) -> None:
    """Initialize binding dialog.

    Args:
        config_manager: ConfigManager instance
        binding: Existing binding to edit (None for new binding)
        parent: Parent window
    """
    super().__init__()

    self.config_manager = config_manager
    self.binding = binding
    # ... rest unchanged

# Update _on_save_clicked:
def _on_save_clicked(self, button: Gtk.Button) -> None:
    """Handle save button click."""
    new_binding = self.get_binding()

    if self.binding:
        # Update existing
        result = self.config_manager.update_binding(self.binding, new_binding)
    else:
        # Add new
        result = self.config_manager.add_binding(new_binding)

    if result.success:
        # Save to disk
        self.config_manager.save()
        self.close()
    else:
        # Show error dialog
        error_dialog = Adw.MessageDialog.new(self)
        error_dialog.set_heading("Error")
        error_dialog.set_body(result.message)

        if result.conflicts:
            conflicts_text = "\n".join([
                f"- {c.description} ({c.modifiers} + {c.key})"
                for c in result.conflicts
            ])
            error_dialog.set_body(
                f"{result.message}\n\nConflicting bindings:\n{conflicts_text}"
            )

        error_dialog.add_response("ok", "OK")
        error_dialog.present()
```

6. **Update EditorTab to pass config_manager**:
```python
# In _on_add_clicked and _on_edit_clicked:
dialog = BindingDialog(config_manager=self.config_manager, binding=binding, parent=self.get_root())
```

7. **Verify tests pass**:
```bash
pytest tests/core/test_config_writer.py tests/core/test_config_manager.py -v
```

8. **Manual verification**:
```bash
cd /home/komi/repos/hyprbind/worktrees/dev
.venv/bin/python -m hyprbind
# Add a binding, save should write to disk
# Check the config file was updated
```

9. **Commit**:
```bash
git add src/hyprbind/core/config_writer.py tests/core/test_config_writer.py src/hyprbind/core/config_manager.py src/hyprbind/ui/
git commit -m "feat: Add config file writer

Implement ConfigWriter to save modifications:
- Generates Hyprland config format
- Groups bindings by category with headers
- Preserves bindd format with descriptions
- Integrates with ConfigManager.save()
- Connected to binding dialog save action

Users can now add/edit/delete bindings and save changes to disk.
Config file is properly formatted with category headers.

Tests: 3 new tests for writer
Coverage: ConfigWriter and save integration

🤖 Generated with Claude Code
https://claude.com/claude-code"
```

---

### Tasks 16-19: Additional Phase 6 Features

**Task 16**: Backup system infrastructure
**Task 17**: Chezmoi integration
**Task 18**: GitHub profile fetcher (with Firecrawl MCP)
**Task 19**: Export engine (markdown/PDF/HTML)

*(Detailed TDD steps for these tasks follow the same pattern as above, with tests → fail → implement → pass → commit)*

---

## Phase 7: Advanced Features (Tasks 20-24)

### Task 20: Hyprland IPC Client
**Goal**: Communication with running Hyprland instance

### Task 21: Mode Manager (Safe/Live Toggle)
**Goal**: Safe mode (file only) vs Live mode (IPC testing)

### Task 22: Live Mode Testing
**Goal**: Test bindings on running Hyprland without saving

### Task 23: Wallust Integration
**Goal**: Load dynamic colors from Wallust

### Task 24: Dynamic Theme System
**Goal**: Apply colors to GTK4 widgets

*(Detailed TDD steps for these tasks follow the same pattern)*

---

## Parallelization Strategy

**Batch 4 (Tabs - Tasks 9-14):**
- Group 1: Tasks 9, 10, 11 (Editor tab - sequential due to dependencies)
- Group 2: Task 12 (Reference - independent)
- Group 3: Task 13 (Community - independent)
- Group 4: Task 14 (Cheatsheet - independent)

Execute: Tasks 9 first, then 10-11 in sequence, then 12-14 in parallel (3 agents)

**Batch 5 (Backend - Tasks 15-19):**
- Task 15: Config writer (sequential - needed by others)
- Group 1: Tasks 16-17 (Backup - can run together)
- Group 2: Task 18 (GitHub fetcher - independent)
- Group 3: Task 19 (Export engine - independent)

Execute: Task 15 first, then 16-19 in parallel (4 agents if possible, or 2 batches)

**Batch 6 (Advanced - Tasks 20-24):**
- Group 1: Tasks 20-21 (IPC + Mode Manager - related)
- Task 22: Live testing (depends on 20-21)
- Group 2: Tasks 23-24 (Wallust + Theme - related)

Execute: 20-21 in parallel, then 22, then 23-24 in parallel

---

## Success Criteria

**Phase 5 Complete:**
- ✅ 4 functional tabs with navigation
- ✅ Editor tab displays and manages bindings
- ✅ Reference tab shows searchable documentation
- ✅ Community tab has GitHub input (functional in Phase 6)
- ✅ Cheatsheet tab displays visual grid
- ✅ All UI tests passing
- ✅ Manual verification successful

**Phase 6 Complete:**
- ✅ Config changes persist to disk
- ✅ Backup system functional
- ✅ GitHub fetching works
- ✅ Export to markdown/PDF/HTML
- ✅ Integration tests passing

**Phase 7 Complete:**
- ✅ Hyprland IPC communication works
- ✅ Safe/Live mode toggle functional
- ✅ Live testing works without file changes
- ✅ Wallust colors loaded and applied
- ✅ Theme updates dynamically
- ✅ End-to-end workflow tests passing

---

## Estimated Timeline

- **Phase 5** (6 tasks): ~90-120 minutes
- **Code Review**: ~30 minutes
- **Phase 6** (5 tasks): ~75-100 minutes
- **Code Review**: ~30 minutes
- **Phase 7** (5 tasks): ~75-100 minutes
- **Final Review**: ~30 minutes
- **Polish & Documentation**: ~60 minutes

**Total Estimate**: 6-8 hours of development time

---

## Next Steps

1. Review this plan
2. Execute Phase 5 tasks (9-14)
3. Code review batch
4. Execute Phase 6 tasks (15-19)
5. Code review batch
6. Execute Phase 7 tasks (20-24)
7. Final code review
8. End-to-end testing
9. Documentation
10. Release preparation

