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
        """Check if this binding conflicts with another."""
        # Same modifiers and key = conflict
        return (
            self.modifiers == other.modifiers
            and self.key == other.key
            and self.submap == other.submap
        )


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

    def add_binding(self, binding: Binding) -> None:
        """Add binding to appropriate category."""
        if binding.category not in self.categories:
            self.categories[binding.category] = Category(name=binding.category)
        self.categories[binding.category].bindings.append(binding)

    def get_all_bindings(self) -> List[Binding]:
        """Get flat list of all bindings."""
        all_bindings = []
        for category in self.categories.values():
            all_bindings.extend(category.bindings)
        return all_bindings
