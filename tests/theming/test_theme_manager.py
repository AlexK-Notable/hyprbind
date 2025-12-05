"""Tests for ThemeManager (Task 24)."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from gi.repository import Gtk, Gdk

from hyprbind.theming.theme_manager import ThemeManager
from hyprbind.theming.wallust_loader import ColorPalette


class TestThemeManager:
    """Test ThemeManager class."""

    def test_theme_manager_creation(self):
        """Create ThemeManager instance."""
        manager = ThemeManager()
        assert manager is not None
        assert manager.css_provider is None
        assert manager.current_palette is None

    def test_generate_css_from_palette(self):
        """Generate CSS from color palette."""
        palette = ColorPalette(
            background="#1e1e2e",
            foreground="#cdd6f4",
            accent="#89b4fa"
        )

        manager = ThemeManager()
        css = manager.generate_css(palette)

        # Check CSS contains color definitions
        assert "@define-color background_color #1e1e2e" in css
        assert "@define-color foreground_color #cdd6f4" in css
        assert "@define-color accent_color #89b4fa" in css

    def test_generate_css_with_numbered_colors(self):
        """Generate CSS including numbered colors."""
        palette = ColorPalette(
            background="#1e1e2e",
            foreground="#cdd6f4",
            accent="#89b4fa",
            color0="#000000",
            color1="#ff0000",
            color2="#00ff00"
        )

        manager = ThemeManager()
        css = manager.generate_css(palette)

        assert "@define-color color0 #000000" in css
        assert "@define-color color1 #ff0000" in css
        assert "@define-color color2 #00ff00" in css

    def test_css_includes_widget_styles(self):
        """Generated CSS includes widget styling rules."""
        palette = ColorPalette(
            background="#1e1e2e",
            foreground="#cdd6f4",
            accent="#89b4fa"
        )

        manager = ThemeManager()
        css = manager.generate_css(palette)

        # Check for widget selectors
        assert "window {" in css
        assert "headerbar {" in css
        assert ".accent {" in css

    @patch('hyprbind.theming.theme_manager.Gdk.Display.get_default')
    @patch('hyprbind.theming.theme_manager.Gtk.StyleContext.add_provider_for_display')
    def test_apply_theme(self, mock_add_provider, mock_get_display):
        """Apply theme to GTK display."""
        # Setup mocks
        mock_display = MagicMock()
        mock_get_display.return_value = mock_display

        palette = ColorPalette(
            background="#1e1e2e",
            foreground="#cdd6f4",
            accent="#89b4fa"
        )

        manager = ThemeManager()
        result = manager.apply_theme(palette)

        assert result is True
        assert manager.current_palette == palette
        assert manager.css_provider is not None
        mock_add_provider.assert_called_once()

    @patch('hyprbind.theming.theme_manager.Gdk.Display.get_default')
    def test_apply_theme_no_display(self, mock_get_display):
        """Handle case when display is not available."""
        mock_get_display.return_value = None

        palette = ColorPalette(
            background="#1e1e2e",
            foreground="#cdd6f4",
            accent="#89b4fa"
        )

        manager = ThemeManager()
        result = manager.apply_theme(palette)

        assert result is False

    @patch('hyprbind.theming.theme_manager.Gdk.Display.get_default')
    @patch('hyprbind.theming.theme_manager.Gtk.StyleContext.remove_provider_for_display')
    def test_apply_theme_with_none_uses_default(self, mock_remove_provider, mock_get_display):
        """Use default theme when None palette provided."""
        mock_display = MagicMock()
        mock_get_display.return_value = mock_display

        manager = ThemeManager()

        # First apply a theme
        palette = ColorPalette(
            background="#1e1e2e",
            foreground="#cdd6f4",
            accent="#89b4fa"
        )
        with patch('hyprbind.theming.theme_manager.Gtk.StyleContext.add_provider_for_display'):
            manager.apply_theme(palette)

        # Now apply None to reset
        result = manager.apply_theme(None)

        assert result is True
        assert manager.current_palette is None
        assert manager.css_provider is None
        mock_remove_provider.assert_called_once()

    def test_reload_theme_with_current_palette(self):
        """Reload theme using current palette."""
        palette = ColorPalette(
            background="#1e1e2e",
            foreground="#cdd6f4",
            accent="#89b4fa"
        )

        manager = ThemeManager()
        manager.current_palette = palette

        with patch.object(manager, 'apply_theme', return_value=True) as mock_apply:
            result = manager.reload_theme()

            assert result is True
            mock_apply.assert_called_once_with(palette)

    def test_reload_theme_without_palette(self):
        """Reload theme when no palette is set."""
        manager = ThemeManager()
        result = manager.reload_theme()

        assert result is True


class TestCSSGeneration:
    """Test CSS generation logic in detail."""

    def test_css_color_variable_format(self):
        """CSS color variables use correct format."""
        palette = ColorPalette(
            background="#1e1e2e",
            foreground="#cdd6f4",
            accent="#89b4fa"
        )

        manager = ThemeManager()
        css = manager.generate_css(palette)

        # Variables should use @define-color syntax
        lines = css.split('\n')
        color_lines = [l for l in lines if l.strip().startswith('@define-color')]

        assert len(color_lines) >= 3  # At least background, foreground, accent

    def test_css_window_styling(self):
        """Window element receives background and foreground colors."""
        palette = ColorPalette(
            background="#1e1e2e",
            foreground="#cdd6f4",
            accent="#89b4fa"
        )

        manager = ThemeManager()
        css = manager.generate_css(palette)

        assert "window {" in css
        assert "background-color: @background_color" in css
        assert "color: @foreground_color" in css

    def test_css_headerbar_styling(self):
        """Headerbar receives custom styling."""
        palette = ColorPalette(
            background="#1e1e2e",
            foreground="#cdd6f4",
            accent="#89b4fa"
        )

        manager = ThemeManager()
        css = manager.generate_css(palette)

        assert "headerbar {" in css

    def test_css_accent_class(self):
        """CSS includes .accent class for accent colors."""
        palette = ColorPalette(
            background="#1e1e2e",
            foreground="#cdd6f4",
            accent="#89b4fa"
        )

        manager = ThemeManager()
        css = manager.generate_css(palette)

        assert ".accent {" in css
        assert "color: @accent_color" in css

    def test_css_includes_all_numbered_colors(self):
        """All numbered colors from palette are included in CSS."""
        palette = ColorPalette(
            background="#1e1e2e",
            foreground="#cdd6f4",
            accent="#89b4fa",
            color0="#000000",
            color1="#111111",
            color2="#222222",
            color3="#333333",
            color4="#444444",
            color5="#555555",
            color6="#666666",
            color7="#777777",
            color8="#888888",
            color9="#999999",
            color10="#aaaaaa",
            color11="#bbbbbb",
            color12="#cccccc",
            color13="#dddddd",
            color14="#eeeeee",
            color15="#ffffff"
        )

        manager = ThemeManager()
        css = manager.generate_css(palette)

        for i in range(16):
            assert f"@define-color color{i}" in css


class TestThemeManagerIntegration:
    """Integration tests for theme manager."""

    @patch('hyprbind.theming.theme_manager.Gdk.Display.get_default')
    @patch('hyprbind.theming.theme_manager.Gtk.StyleContext.add_provider_for_display')
    def test_complete_theme_application_workflow(self, mock_add_provider, mock_get_display):
        """Test complete workflow from palette to applied theme."""
        mock_display = MagicMock()
        mock_get_display.return_value = mock_display

        # Create palette
        palette = ColorPalette(
            background="#1e1e2e",
            foreground="#cdd6f4",
            accent="#89b4fa",
            color0="#45475a",
            color1="#f38ba8",
            color2="#a6e3a1"
        )

        # Apply theme
        manager = ThemeManager()
        result = manager.apply_theme(palette)

        # Verify
        assert result is True
        assert manager.current_palette == palette
        assert manager.css_provider is not None

        # Verify CSS was generated and loaded
        call_args = mock_add_provider.call_args
        assert call_args is not None

    @patch('hyprbind.theming.theme_manager.Gdk.Display.get_default')
    @patch('hyprbind.theming.theme_manager.Gtk.StyleContext.add_provider_for_display')
    def test_theme_switching(self, mock_add_provider, mock_get_display):
        """Test switching between different themes."""
        mock_display = MagicMock()
        mock_get_display.return_value = mock_display

        manager = ThemeManager()

        # Apply first theme
        palette1 = ColorPalette(
            background="#1e1e2e",
            foreground="#cdd6f4",
            accent="#89b4fa"
        )
        manager.apply_theme(palette1)
        assert manager.current_palette == palette1

        # Apply second theme
        palette2 = ColorPalette(
            background="#000000",
            foreground="#ffffff",
            accent="#ff0000"
        )
        manager.apply_theme(palette2)
        assert manager.current_palette == palette2

        # Verify provider was updated (called twice)
        assert mock_add_provider.call_count == 2
