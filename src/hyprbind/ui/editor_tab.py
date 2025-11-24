"""Editor tab for managing keybindings with category grouping."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Gio, GObject, Adw, GLib
from typing import Optional

from hyprbind.core.config_manager import ConfigManager
from hyprbind.core.mode_manager import ModeManager
from hyprbind.core.models import Binding
from hyprbind.ui.binding_dialog import BindingDialog


class BindingWithSection(GObject.Object):
    """Wrapper for binding or section header in the list."""

    # GObject properties
    binding: Binding = GObject.Property(type=object, default=None)
    is_header: bool = GObject.Property(type=bool, default=False)
    header_text: str = GObject.Property(type=str, default="")

    def __init__(
        self,
        binding: Optional[Binding] = None,
        is_header: bool = False,
        header_text: str = "",
    ) -> None:
        """Initialize wrapper.

        Args:
            binding: Binding object (for binding items)
            is_header: True if this is a category header
            header_text: Text for category header
        """
        super().__init__()
        self.binding = binding
        self.is_header = is_header
        self.header_text = header_text


class EditorTab(Gtk.Box):
    """Editor tab displaying bindings with category grouping."""

    def __init__(self, config_manager: ConfigManager, mode_manager: ModeManager) -> None:
        """Initialize the editor tab.

        Args:
            config_manager: ConfigManager instance for loading bindings
            mode_manager: ModeManager instance for Safe/Live mode operations
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.config_manager = config_manager
        self.mode_manager = mode_manager

        # Create list store for BindingWithSection objects
        self.list_store = Gio.ListStore.new(BindingWithSection)
        self.selection_model = Gtk.SingleSelection.new(self.list_store)

        # Create list view
        self.list_view = Gtk.ListView.new(self.selection_model, None)

        # Create factory for list items
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._on_factory_setup)
        factory.connect("bind", self._on_factory_bind)
        self.list_view.set_factory(factory)

        # Scrolled window for list view
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_child(self.list_view)
        self.append(scrolled)

        # Toolbar
        toolbar = self._create_toolbar()
        self.prepend(toolbar)

        # Register as observer for config changes
        # Wrap callback to ensure it runs on main thread (GTK requirement)
        self.config_manager.add_observer(lambda: GLib.idle_add(self.reload_bindings))

        # Initial load
        self.reload_bindings()

    def _create_toolbar(self) -> Gtk.Box:
        """Create toolbar with CRUD buttons.

        Returns:
            Toolbar widget with Add/Edit/Delete buttons
        """
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        toolbar.set_margin_start(6)
        toolbar.set_margin_end(6)
        toolbar.set_margin_top(6)
        toolbar.set_margin_bottom(6)

        # Add button
        self.add_button = Gtk.Button(label="Add")
        self.add_button.set_icon_name("list-add-symbolic")
        self.add_button.connect("clicked", self._on_add_clicked)
        toolbar.append(self.add_button)

        # Edit button
        self.edit_button = Gtk.Button(label="Edit")
        self.edit_button.set_icon_name("document-edit-symbolic")
        self.edit_button.connect("clicked", self._on_edit_clicked)
        toolbar.append(self.edit_button)

        # Delete button
        self.delete_button = Gtk.Button(label="Delete")
        self.delete_button.set_icon_name("user-trash-symbolic")
        self.delete_button.connect("clicked", self._on_delete_clicked)
        toolbar.append(self.delete_button)

        return toolbar

    def _on_factory_setup(self, factory: Gtk.SignalListItemFactory, list_item: Gtk.ListItem) -> None:
        """Setup list item widget structure (supports headers and bindings).

        Args:
            factory: The factory creating the item
            list_item: List item being setup
        """
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # Header label (for category headers)
        header = Gtk.Label()
        header.set_name("header_label")
        header.add_css_class("heading")
        header.set_xalign(0)
        header.set_margin_start(12)
        header.set_margin_top(12)
        header.set_margin_bottom(6)
        box.append(header)

        # Binding box (for binding items)
        binding_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        binding_box.set_name("binding_box")
        binding_box.set_margin_start(12)
        binding_box.set_margin_end(12)
        binding_box.set_margin_top(6)
        binding_box.set_margin_bottom(6)

        # Key label
        key_label = Gtk.Label()
        key_label.set_name("key_label")
        key_label.set_width_chars(20)
        key_label.set_xalign(0)
        binding_box.append(key_label)

        # Description label
        desc_label = Gtk.Label()
        desc_label.set_name("desc_label")
        desc_label.set_hexpand(True)
        desc_label.set_xalign(0)
        binding_box.append(desc_label)

        # Action label
        action_label = Gtk.Label()
        action_label.set_name("action_label")
        action_label.set_width_chars(30)
        action_label.set_xalign(0)
        action_label.add_css_class("dim-label")
        binding_box.append(action_label)

        box.append(binding_box)
        list_item.set_child(box)

    def _on_factory_bind(self, factory: Gtk.SignalListItemFactory, list_item: Gtk.ListItem) -> None:
        """Bind data to list item (handles both headers and bindings).

        Args:
            factory: The factory binding the item
            list_item: List item being bound
        """
        item = list_item.get_item()
        box = list_item.get_child()

        # Find widgets
        header_label = None
        binding_box = None
        child = box.get_first_child()
        while child:
            if child.get_name() == "header_label":
                header_label = child
            elif child.get_name() == "binding_box":
                binding_box = child
            child = child.get_next_sibling()

        if item.is_header:
            # Show header, hide binding
            header_label.set_visible(True)
            header_label.set_text(item.header_text)
            binding_box.set_visible(False)
        else:
            # Hide header, show binding
            header_label.set_visible(False)
            binding_box.set_visible(True)

            binding = item.binding

            # Find labels in binding_box
            key_label = None
            desc_label = None
            action_label = None
            child = binding_box.get_first_child()
            while child:
                name = child.get_name()
                if name == "key_label":
                    key_label = child
                elif name == "desc_label":
                    desc_label = child
                elif name == "action_label":
                    action_label = child
                child = child.get_next_sibling()

            # Set binding text
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

    def reload_bindings(self) -> None:
        """Reload bindings from config (called by observer pattern)."""
        self.list_store.remove_all()

        if not self.config_manager.config:
            return

        # Load with category headers
        for category in sorted(self.config_manager.config.categories.keys()):
            category_obj = self.config_manager.config.categories[category]
            bindings = category_obj.bindings

            if not bindings:
                continue

            # Add header
            self.list_store.append(
                BindingWithSection(is_header=True, header_text=category)
            )

            # Add bindings
            for binding in bindings:
                self.list_store.append(BindingWithSection(binding=binding))

    def _on_add_clicked(self, button: Gtk.Button) -> None:
        """Handle Add button click - show dialog for new binding.

        Args:
            button: The button that was clicked
        """
        dialog = BindingDialog(
            config_manager=self.config_manager,
            mode_manager=self.mode_manager,
            parent=self.get_root(),
        )
        dialog.present()

    def _on_edit_clicked(self, button: Gtk.Button) -> None:
        """Handle Edit button click - show dialog for selected binding.

        Args:
            button: The button that was clicked
        """
        position = self.selection_model.get_selected()
        if position == Gtk.INVALID_LIST_POSITION:
            return

        item = self.selection_model.get_selected_item()
        if item.is_header:
            return  # Can't edit header

        binding = item.binding

        dialog = BindingDialog(
            config_manager=self.config_manager,
            mode_manager=self.mode_manager,
            binding=binding,
            parent=self.get_root(),
        )
        dialog.present()

    def _on_delete_clicked(self, button: Gtk.Button) -> None:
        """Handle Delete button click - show confirmation dialog.

        Args:
            button: The button that was clicked
        """
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

    def _on_delete_response(
        self, dialog: Adw.MessageDialog, response: str, binding: Binding
    ) -> None:
        """Handle delete confirmation dialog response.

        Args:
            dialog: The dialog emitting the response
            response: Response ID ("delete" or "cancel")
            binding: Binding to delete
        """
        if response == "delete":
            result = self.config_manager.remove_binding(binding)
            if result.success:
                self.config_manager.save()
