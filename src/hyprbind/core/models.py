"""Data models for Hyprland keybindings."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class BindType(Enum):
    """Types of Hyprland keybindings."""

    BINDD = "bindd"  # Documented binding
    BIND = "bind"  # Standard binding
    BINDEL = "bindel"  # Repeatable binding (on hold)
    BINDM = "bindm"  # Mouse binding


@dataclass
class Binding:
    """Represents a single Hyprland keybinding."""

    type: BindType
    modifiers: List[str]
    key: str
    description: str
    action: str
    params: str
    submap: Optional[str]
    line_number: int
    category: str

    @property
    def display_name(self) -> str:
        """Human-readable keybinding representation (e.g., 'Super + Q')."""
        # Map variable names to readable names
        readable_mods = []
        for mod in self.modifiers:
            if mod == "$mainMod":
                readable_mods.append("Super")
            elif mod == "SHIFT":
                readable_mods.append("Shift")
            elif mod == "CTRL":
                readable_mods.append("Ctrl")
            elif mod == "ALT":
                readable_mods.append("Alt")
            else:
                readable_mods.append(mod)

        if readable_mods:
            return " + ".join(readable_mods) + " + " + self.key
        return self.key

    def conflicts_with(self, other: "Binding") -> bool:
        """
        Check if this binding conflicts with another.

        Note: Modifier order is normalized, so 'SHIFT + SUPER' and 'SUPER + SHIFT'
        are treated as the same combination.
        """
        # Sort modifiers to handle different orderings (SHIFT+SUPER == SUPER+SHIFT)
        return (
            sorted(self.modifiers) == sorted(other.modifiers)
            and self.key == other.key
            and self.submap == other.submap
        )

    @property
    def conflict_key(self) -> tuple:
        """Generate hash key for conflict detection.

        Returns:
            Tuple of (sorted_modifiers, key, submap) for consistent hashing.
            Modifiers are sorted to ensure 'SHIFT+SUPER' == 'SUPER+SHIFT'.
        """
        return (tuple(sorted(self.modifiers)), self.key, self.submap)


@dataclass
class Category:
    """Organizes bindings into groups."""

    name: str
    bindings: List[Binding] = field(default_factory=list)
    icon: str = "folder-symbolic"
    description: str = ""
    collapsed: bool = False


@dataclass
class Config:
    """Complete Hyprland keybinding configuration."""

    categories: dict[str, Category] = field(default_factory=dict)
    variables: dict[str, str] = field(default_factory=dict)
    submaps: dict[str, List[Binding]] = field(default_factory=dict)
    file_path: Optional[str] = None
    original_content: str = ""
    _binding_index: dict[tuple, Binding] = field(default_factory=dict, repr=False)

    def add_binding(self, binding: Binding) -> None:
        """Add binding to appropriate category and update index.

        Note: Caller should check for conflicts before adding (use find_conflict()).
        If a binding with the same conflict_key exists, this overwrites the index
        entry - use ConfigManager.add_binding() for conflict-safe operations.
        """
        if binding.category not in self.categories:
            self.categories[binding.category] = Category(name=binding.category)
        self.categories[binding.category].bindings.append(binding)
        # Update conflict detection index
        self._binding_index[binding.conflict_key] = binding

    def remove_binding(self, binding: Binding) -> None:
        """Remove binding from category and update index."""
        if binding.category in self.categories:
            category = self.categories[binding.category]
            if binding in category.bindings:
                category.bindings.remove(binding)
        # Update conflict detection index
        self._binding_index.pop(binding.conflict_key, None)

    def find_conflict(self, binding: Binding) -> Optional[Binding]:
        """Find conflicting binding in O(1) time.

        Args:
            binding: Binding to check for conflicts

        Returns:
            Conflicting binding if found, None otherwise
        """
        return self._binding_index.get(binding.conflict_key)

    def get_all_bindings(self) -> List[Binding]:
        """Get flat list of all bindings."""
        all_bindings = []
        for category in self.categories.values():
            all_bindings.extend(category.bindings)
        return all_bindings

    def rebuild_index(self) -> None:
        """Rebuild the binding index from all categories.

        Use this if bindings were added/removed without using add_binding/remove_binding,
        or to ensure index consistency after deserialization.
        """
        self._binding_index.clear()
        for category in self.categories.values():
            for binding in category.bindings:
                self._binding_index[binding.conflict_key] = binding
