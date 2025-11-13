#!/usr/bin/env python3
"""Visual test for dynamic theme system."""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw
from hyprbind.theming import WallustLoader, ThemeManager, ColorPalette


def on_activate(app):
    """Create test window with dynamic theme."""
    # Create window
    window = Adw.ApplicationWindow(application=app)
    window.set_title("HyprBind Theme Test")
    window.set_default_size(600, 400)

    # Create theme manager
    theme_manager = ThemeManager()

    # Create content box
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
    box.set_margin_top(20)
    box.set_margin_bottom(20)
    box.set_margin_start(20)
    box.set_margin_end(20)

    # Add header
    header = Gtk.Label(label="Dynamic Theme System Test")
    header.add_css_class("title-1")
    box.append(header)

    # Check Wallust installation
    if WallustLoader.is_installed():
        status = Gtk.Label(label="✓ Wallust is installed")
        status.add_css_class("success")
    else:
        status = Gtk.Label(label="✗ Wallust not installed")
        status.add_css_class("error")
    box.append(status)

    # Try to load colors
    palette = WallustLoader.load_colors()
    if palette:
        colors_label = Gtk.Label(label=f"✓ Loaded colors from Wallust")
        colors_label.add_css_class("success")
        box.append(colors_label)

        # Show color values
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        info_box.add_css_class("card")
        info_box.set_margin_top(10)

        bg_label = Gtk.Label(label=f"Background: {palette.background}")
        fg_label = Gtk.Label(label=f"Foreground: {palette.foreground}")
        accent_label = Gtk.Label(label=f"Accent: {palette.accent}")
        accent_label.add_css_class("accent")

        info_box.append(bg_label)
        info_box.append(fg_label)
        info_box.append(accent_label)
        box.append(info_box)

        # Apply theme
        if theme_manager.apply_theme(palette):
            applied_label = Gtk.Label(label="✓ Theme applied successfully")
            applied_label.add_css_class("success")
            box.append(applied_label)
        else:
            error_label = Gtk.Label(label="✗ Failed to apply theme")
            error_label.add_css_class("error")
            box.append(error_label)
    else:
        no_colors = Gtk.Label(label="✗ No Wallust colors found")
        no_colors.add_css_class("warning")
        box.append(no_colors)

        # Create sample palette for testing
        sample_palette = ColorPalette(
            background="#1e1e2e",
            foreground="#cdd6f4",
            accent="#89b4fa",
            color0="#45475a",
            color1="#f38ba8",
            color2="#a6e3a1"
        )

        sample_label = Gtk.Label(label="Using sample palette for testing")
        box.append(sample_label)

        if theme_manager.apply_theme(sample_palette):
            applied_label = Gtk.Label(label="✓ Sample theme applied")
            applied_label.add_css_class("success")
            box.append(applied_label)

    # Add test buttons
    button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    button_box.set_margin_top(20)
    button_box.set_halign(Gtk.Align.CENTER)

    normal_button = Gtk.Button(label="Normal Button")
    accent_button = Gtk.Button(label="Accent Button")
    accent_button.add_css_class("accent")
    success_button = Gtk.Button(label="Success Button")
    success_button.add_css_class("success")

    button_box.append(normal_button)
    button_box.append(accent_button)
    button_box.append(success_button)
    box.append(button_box)

    # Set content
    window.set_content(box)
    window.present()


def main():
    """Run the test application."""
    app = Adw.Application(application_id="dev.hyprbind.theme_test")
    app.connect("activate", on_activate)
    app.run(None)


if __name__ == "__main__":
    main()
