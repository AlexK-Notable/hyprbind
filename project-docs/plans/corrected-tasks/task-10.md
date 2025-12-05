# Task 10: Editor Tab - Binding List (CORRECTED)
**Corrections Applied**: Category grouping, observer registration, reload mechanism

---

## Key Change: Category Grouping with Section Headers

**BindingWithSection wrapper** (`src/hyprbind/ui/editor_tab.py`):
```python
from gi.repository import Gtk, Gio, GObject

class BindingWithSection(GObject.Object):
    """Wrapper for binding or section header."""
    binding: Binding = GObject.Property(type=object)
    is_header: bool = GObject.Property(type=bool, default=False)
    header_text: str = GObject.Property(type=str, default="")

    def __init__(self, binding: Optional[Binding] = None,
                 is_header: bool = False, header_text: str = "") -> None:
        super().__init__()
        self.binding = binding
        self.is_header = is_header
        self.header_text = header_text


class EditorTab(Gtk.Box):
    def __init__(self, config_manager: ConfigManager) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.config_manager = config_manager

        # Create list store for BindingWithSection objects
        self.list_store = Gio.ListStore.new(BindingWithSection)
        self.selection_model = Gtk.SingleSelection.new(self.list_store)

        # Create list view
        self.list_view = Gtk.ListView.new(self.selection_model, None)

        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._on_factory_setup)
        factory.connect("bind", self._on_factory_bind)
        self.list_view.set_factory(factory)

        # Scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_child(self.list_view)
        self.append(scrolled)

        # Toolbar
        toolbar = self._create_toolbar()
        self.prepend(toolbar)

        # Register as observer
        self.config_manager.add_observer(self.reload_bindings)

        # Initial load
        self.reload_bindings()

    def _on_factory_setup(self, factory, list_item):
        """Setup supports headers and bindings."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # Header label
        header = Gtk.Label()
        header.set_name("header_label")
        header.add_css_class("heading")
        header.set_xalign(0)
        header.set_margin_start(12)
        header.set_margin_top(12)
        header.set_margin_bottom(6)
        box.append(header)

        # Binding box
        binding_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        binding_box.set_name("binding_box")
        binding_box.set_margin_start(12)
        binding_box.set_margin_end(12)
        binding_box.set_margin_top(6)
        binding_box.set_margin_bottom(6)

        key_label = Gtk.Label()
        key_label.set_name("key_label")
        key_label.set_width_chars(20)
        key_label.set_xalign(0)
        binding_box.append(key_label)

        desc_label = Gtk.Label()
        desc_label.set_name("desc_label")
        desc_label.set_hexpand(True)
        desc_label.set_xalign(0)
        binding_box.append(desc_label)

        action_label = Gtk.Label()
        action_label.set_name("action_label")
        action_label.set_width_chars(30)
        action_label.set_xalign(0)
        action_label.add_css_class("dim-label")
        binding_box.append(action_label)

        box.append(binding_box)
        list_item.set_child(box)

    def _on_factory_bind(self, factory, list_item):
        """Bind header or binding."""
        item = list_item.get_item()
        box = list_item.get_child()

        # Find widgets
        header_label = binding_box = None
        child = box.get_first_child()
        while child:
            if child.get_name() == "header_label":
                header_label = child
            elif child.get_name() == "binding_box":
                binding_box = child
            child = child.get_next_sibling()

        if item.is_header:
            # Show header
            header_label.set_visible(True)
            header_label.set_text(item.header_text)
            binding_box.set_visible(False)
        else:
            # Show binding
            header_label.set_visible(False)
            binding_box.set_visible(True)

            binding = item.binding

            # Find labels in binding_box
            key_label = desc_label = action_label = None
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
        """Reload bindings from config - called by observer."""
        self.list_store.remove_all()

        if not self.config_manager.config:
            return

        # Load with category headers
        for category in sorted(self.config_manager.config.categories.keys()):
            bindings = self.config_manager.config.categories[category]

            if not bindings:
                continue

            # Add header
            self.list_store.append(BindingWithSection(
                is_header=True,
                header_text=category
            ))

            # Add bindings
            for binding in bindings:
                self.list_store.append(BindingWithSection(binding=binding))

    # Toolbar methods unchanged from original plan
```

**Tests** (`tests/ui/test_editor_tab.py`):
```python
# Use direct references
def test_editor_tab_has_list_view(manager):
    tab = EditorTab(manager)
    assert tab.list_view is not None

def test_editor_tab_has_category_headers(manager):
    tab = EditorTab(manager)

    # Count headers
    headers = []
    for i in range(tab.list_store.get_n_items()):
        item = tab.list_store.get_item(i)
        if item.is_header:
            headers.append(item.header_text)

    assert len(headers) > 0
    assert "Window Actions" in headers
```

---

Key: Category grouping with section headers, observer pattern for auto-reload.
