"""Dynamic theme management for GTK4 application (Task 24)."""

from typing import Optional
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk

from hyprbind.theming.wallust_loader import ColorPalette
from hyprbind.core.logging_config import get_logger

logger = get_logger(__name__)


class ThemeManager:
    """Manages dynamic theming for the application.

    Applies Wallust colors to GTK4 widgets throughout the application
    using CSS custom properties and GtkCssProvider.
    """

    def __init__(self):
        """Initialize theme manager."""
        self.css_provider: Optional[Gtk.CssProvider] = None
        self.current_palette: Optional[ColorPalette] = None

    def generate_css(self, palette: ColorPalette) -> str:
        """Generate CSS from color palette.

        Creates CSS with @define-color variables and widget styles
        that use the Wallust color palette.

        Args:
            palette: Color palette to generate CSS from

        Returns:
            CSS string with color definitions and widget styles
        """
        css_parts = []

        # Header comment
        css_parts.append("/* Wallust Dynamic Colors */")

        # Define primary color variables
        css_parts.append(f"@define-color background_color {palette.background};")
        css_parts.append(f"@define-color foreground_color {palette.foreground};")
        css_parts.append(f"@define-color accent_color {palette.accent};")

        # Add numbered colors if available (color0-15)
        for i in range(16):
            color = getattr(palette, f"color{i}", None)
            if color:
                css_parts.append(f"@define-color color{i} {color};")

        css_parts.append("")

        # Widget styling
        css_parts.append("/* Widget Styles */")

        # Window background and foreground
        css_parts.append("window {")
        css_parts.append("    background-color: @background_color;")
        css_parts.append("    color: @foreground_color;")
        css_parts.append("}")
        css_parts.append("")

        # Headerbar with subtle blend
        css_parts.append("headerbar {")
        css_parts.append("    background-color: mix(@background_color, @foreground_color, 0.95);")
        css_parts.append("}")
        css_parts.append("")

        # Accent class for accent-colored elements
        css_parts.append(".accent {")
        css_parts.append("    color: @accent_color;")
        css_parts.append("}")
        css_parts.append("")

        # Success class using green (color2)
        if palette.color2:
            css_parts.append(".success {")
            css_parts.append("    color: @color2;")
            css_parts.append("}")
            css_parts.append("")

        return "\n".join(css_parts)

    def apply_theme(self, palette: Optional[ColorPalette] = None) -> bool:
        """Apply theme to the application.

        Generates CSS from the palette and applies it to the GTK display
        via GtkCssProvider. If palette is None, reverts to default theme.

        Args:
            palette: Color palette to apply. If None, uses default theme.

        Returns:
            True if theme applied successfully, False otherwise
        """
        if palette is None:
            # Use default/system theme
            return self._apply_default_theme()

        try:
            # Generate CSS from palette
            css = self.generate_css(palette)

            # Create provider if doesn't exist
            if self.css_provider is None:
                self.css_provider = Gtk.CssProvider()

            # Load CSS into provider
            self.css_provider.load_from_data(css.encode())

            # Get default display
            display = Gdk.Display.get_default()
            if display is None:
                return False

            # Apply provider to display
            Gtk.StyleContext.add_provider_for_display(
                display,
                self.css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

            # Store current palette
            self.current_palette = palette

            return True

        except Exception as e:
            logger.error("Failed to apply theme: %s", e)
            return False

    def _apply_default_theme(self) -> bool:
        """Apply default system theme.

        Removes custom CSS provider to revert to system theme.

        Returns:
            True if default theme applied successfully
        """
        if self.css_provider is not None:
            # Remove custom provider
            display = Gdk.Display.get_default()
            if display:
                Gtk.StyleContext.remove_provider_for_display(
                    display,
                    self.css_provider
                )
            self.css_provider = None
            self.current_palette = None

        return True

    def reload_theme(self) -> bool:
        """Reload current theme (useful for live updates).

        Re-applies the current palette if one is set, otherwise
        maintains default theme.

        Returns:
            True if theme reloaded successfully
        """
        if self.current_palette:
            return self.apply_theme(self.current_palette)
        return True
