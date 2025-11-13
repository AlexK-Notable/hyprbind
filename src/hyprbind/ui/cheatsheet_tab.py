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

        # Register as observer for config changes
        self.config_manager.add_observer(self.reload_cheatsheet)

        # Load bindings
        self.reload_cheatsheet()

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

    def _on_factory_setup(
        self, factory: Gtk.SignalListItemFactory, list_item: Gtk.ListItem
    ) -> None:
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

    def _on_factory_bind(
        self, factory: Gtk.SignalListItemFactory, list_item: Gtk.ListItem
    ) -> None:
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

    def reload_cheatsheet(self) -> None:
        """Reload cheatsheet from config (called by observer pattern)."""
        self.list_store.remove_all()

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
