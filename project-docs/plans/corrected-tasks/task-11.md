# Task 11: Editor Tab - CRUD Dialogs (CORRECTED)
**Corrections Applied**: Adw.MessageDialog base, validation, metadata preservation, category/type selectors

---

## BindingDialog (Complete Corrected Implementation)

**File**: `src/hyprbind/ui/binding_dialog.py`

```python
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw
from typing import Optional

from hyprbind.core.config_manager import ConfigManager
from hyprbind.core.models import Binding, BindType


class BindingDialog(Adw.MessageDialog):
    """Dialog for creating or editing a keybinding."""

    def __init__(self, config_manager: ConfigManager,
                 binding: Optional[Binding] = None,
                 parent: Optional[Gtk.Window] = None) -> None:
        super().__init__()

        self.config_manager = config_manager
        self.original_binding = binding  # Store for metadata preservation

        # Dialog setup
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_destroy_with_parent(True)

        self.set_heading("Edit Binding" if binding else "Add Binding")

        # Responses
        self.add_response("cancel", "Cancel")
        self.add_response("save", "Save")
        self.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)

        # Form
        form = self._create_form()
        self.set_extra_child(form)

        if binding:
            self._load_binding(binding)

        self.connect("response", self._on_response)

    def _create_form(self) -> Gtk.Widget:
        """Create form widget."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)

        # Bind type selector
        type_group = Adw.PreferencesGroup()
        self.type_row = Adw.ComboRow()
        self.type_row.set_title("Binding Type")
        types = Gtk.StringList()
        types.append("bindd (with description)")
        types.append("bind (no description)")
        types.append("bindel (on release)")
        types.append("bindm (mouse)")
        self.type_row.set_model(types)
        self.type_row.set_selected(0)
        type_group.add(self.type_row)
        box.append(type_group)

        # Key entry
        key_group = Adw.PreferencesGroup()
        self.key_entry = Adw.EntryRow()
        self.key_entry.set_title("Key")
        key_group.add(self.key_entry)
        box.append(key_group)

        # Modifiers entry
        mod_group = Adw.PreferencesGroup()
        self.modifiers_entry = Adw.EntryRow()
        self.modifiers_entry.set_title("Modifiers (comma-separated)")
        self.modifiers_entry.set_text("$mainMod")
        mod_group.add(self.modifiers_entry)
        box.append(mod_group)

        # Description entry
        desc_group = Adw.PreferencesGroup()
        self.description_entry = Adw.EntryRow()
        self.description_entry.set_title("Description")
        desc_group.add(self.description_entry)
        box.append(desc_group)

        # Action entry
        action_group = Adw.PreferencesGroup()
        self.action_entry = Adw.EntryRow()
        self.action_entry.set_title("Action")
        self.action_entry.set_text("exec")
        action_group.add(self.action_entry)
        box.append(action_group)

        # Params entry
        params_group = Adw.PreferencesGroup()
        self.params_entry = Adw.EntryRow()
        self.params_entry.set_title("Parameters")
        params_group.add(self.params_entry)
        box.append(params_group)

        # Category selector
        cat_group = Adw.PreferencesGroup()
        self.category_row = Adw.ComboRow()
        self.category_row.set_title("Category")

        # Populate categories
        categories = sorted(self.config_manager.config.categories.keys()) if self.config_manager.config else []
        string_list = Gtk.StringList()
        for cat in categories:
            string_list.append(cat)
        string_list.append("Custom")
        self.category_row.set_model(string_list)
        self.category_row.set_selected(len(categories))  # Default to Custom

        cat_group.add(self.category_row)
        box.append(cat_group)

        return box

    def _load_binding(self, binding: Binding) -> None:
        """Load binding data into form."""
        # Bind type
        type_map = {
            BindType.BINDD: 0,
            BindType.BIND: 1,
            BindType.BINDEL: 2,
            BindType.BINDM: 3,
        }
        self.type_row.set_selected(type_map.get(binding.type, 0))

        self.key_entry.set_text(binding.key)

        if binding.modifiers:
            self.modifiers_entry.set_text(", ".join(binding.modifiers))

        if binding.description:
            self.description_entry.set_text(binding.description)

        if binding.action:
            self.action_entry.set_text(binding.action)

        if binding.params:
            self.params_entry.set_text(binding.params)

        # Set category
        if binding.category:
            model = self.category_row.get_model()
            for i in range(model.get_n_items()):
                if model.get_string(i) == binding.category:
                    self.category_row.set_selected(i)
                    break

    def _validate_input(self) -> Optional[str]:
        """Validate form input. Returns error message or None."""
        if not self.key_entry.get_text().strip():
            return "Key cannot be empty"

        if not self.action_entry.get_text().strip():
            return "Action cannot be empty"

        # Validate modifiers
        mod_text = self.modifiers_entry.get_text()
        if mod_text:
            mods = [m.strip() for m in mod_text.split(",")]
            valid_mods = ["SUPER", "SHIFT", "ALT", "CTRL", "$mainMod", "$shiftMod"]
            for mod in mods:
                if mod and mod not in valid_mods and not mod.startswith("$"):
                    return f"Invalid modifier: {mod}"

        return None

    def _on_response(self, dialog: Adw.MessageDialog, response: str) -> None:
        """Handle dialog response."""
        if response == "save":
            # Validate
            error = self._validate_input()
            if error:
                self._show_error(error, [])
                return

            # Get binding
            new_binding = self.get_binding()

            # Save
            if self.original_binding:
                result = self.config_manager.update_binding(self.original_binding, new_binding)
            else:
                result = self.config_manager.add_binding(new_binding)

            if result.success:
                # Save to disk
                self.config_manager.save()
            else:
                # Show error
                conflicts_text = ""
                if result.conflicts:
                    conflicts_text = "\n\nConflicting bindings:\n" + "\n".join([
                        f"- {c.description} ({' + '.join(c.modifiers)} + {c.key})"
                        for c in result.conflicts
                    ])
                self._show_error(result.message + conflicts_text, result.conflicts)

    def _show_error(self, message: str, conflicts: list) -> None:
        """Show error dialog."""
        error = Adw.MessageDialog.new(self.get_transient_for())
        error.set_heading("Error")
        error.set_body(message)
        error.add_response("ok", "OK")
        error.present()

    def get_binding(self) -> Binding:
        """Construct binding from form, preserving metadata."""
        # Parse form
        mod_text = self.modifiers_entry.get_text()
        modifiers = [m.strip() for m in mod_text.split(",") if m.strip()]

        type_idx = self.type_row.get_selected()
        type_map = [BindType.BINDD, BindType.BIND, BindType.BINDEL, BindType.BINDM]
        bind_type = type_map[type_idx]

        # Get category
        cat_model = self.category_row.get_model()
        category = cat_model.get_string(self.category_row.get_selected())

        if self.original_binding:
            # Preserve metadata when editing
            return Binding(
                type=bind_type,
                modifiers=modifiers,
                key=self.key_entry.get_text(),
                description=self.description_entry.get_text(),
                action=self.action_entry.get_text(),
                params=self.params_entry.get_text(),
                submap=self.original_binding.submap,  # Preserve
                line_number=self.original_binding.line_number,  # Preserve
                category=category,
            )
        else:
            # New binding - assign next line number
            next_line = 0
            if self.config_manager.config:
                all_bindings = self.config_manager.config.get_all_bindings()
                if all_bindings:
                    next_line = max([b.line_number for b in all_bindings]) + 1

            return Binding(
                type=bind_type,
                modifiers=modifiers,
                key=self.key_entry.get_text(),
                description=self.description_entry.get_text(),
                action=self.action_entry.get_text(),
                params=self.params_entry.get_text(),
                submap=None,
                line_number=next_line,
                category=category,
            )
```

**EditorTab Wiring** (add to `src/hyprbind/ui/editor_tab.py`):

```python
def _on_add_clicked(self, button: Gtk.Button) -> None:
    dialog = BindingDialog(
        config_manager=self.config_manager,
        parent=self.get_root()
    )
    dialog.present()

def _on_edit_clicked(self, button: Gtk.Button) -> None:
    position = self.selection_model.get_selected()
    if position == Gtk.INVALID_LIST_POSITION:
        return

    item = self.selection_model.get_selected_item()
    if item.is_header:
        return  # Can't edit header

    binding = item.binding

    dialog = BindingDialog(
        config_manager=self.config_manager,
        binding=binding,
        parent=self.get_root()
    )
    dialog.present()

def _on_delete_clicked(self, button: Gtk.Button) -> None:
    position = self.selection_model.get_selected()
    if position == Gtk.INVALID_LIST_POSITION:
        return

    item = self.selection_model.get_selected_item()
    if item.is_header:
        return

    binding = item.binding

    dialog = Adw.MessageDialog.new(self.get_root())
    dialog.set_heading("Delete Binding?")
    dialog.set_body(f"Delete: {binding.description}?")
    dialog.add_response("cancel", "Cancel")
    dialog.add_response("delete", "Delete")
    dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
    dialog.connect("response", self._on_delete_response, binding)
    dialog.present()

def _on_delete_response(self, dialog: Adw.MessageDialog, response: str, binding: Binding) -> None:
    if response == "delete":
        result = self.config_manager.remove_binding(binding)
        if result.success:
            self.config_manager.save()
```

---

Key: Proper dialog, validation, metadata preservation, category/type selectors.
