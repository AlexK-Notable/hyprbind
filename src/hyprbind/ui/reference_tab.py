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

        # Category (optional, small label)
        category_label = Gtk.Label()
        category_label.set_name("category_label")
        category_label.set_xalign(0)
        category_label.add_css_class("caption")
        category_label.add_css_class("dim-label")
        box.append(category_label)

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
        category_label = None

        child = box.get_first_child()
        while child:
            if child.get_name() == "name_label":
                name_label = child
            elif child.get_name() == "desc_label":
                desc_label = child
            elif child.get_name() == "example_label":
                example_label = child
            elif child.get_name() == "category_label":
                category_label = child
            child = child.get_next_sibling()

        # Set text
        if name_label:
            name_label.set_text(action["name"])
        if desc_label:
            desc_label.set_text(action["description"])
        if example_label:
            example_label.set_text(f"Example: {action['example']}")
        if category_label:
            category_label.set_text(f"Category: {action['category']}")

    def _filter_func(self, item: ActionObject, user_data) -> bool:
        """Filter function for search."""
        search_text = self.search_entry.get_text().lower()
        if not search_text:
            return True

        action = item.action
        return (
            search_text in action["name"].lower()
            or search_text in action["description"].lower()
            or search_text in action["category"].lower()
        )

    def _on_search_changed(self, entry: Gtk.SearchEntry) -> None:
        """Handle search text change."""
        self.filter.changed(Gtk.FilterChange.DIFFERENT)
