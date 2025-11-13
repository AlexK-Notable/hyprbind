"""Tests for Wallust color loader."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import tempfile
import shutil
import os

from hyprbind.theming.wallust_loader import WallustLoader, ColorPalette


class TestWallustDetection:
    """Test Wallust installation and config detection."""

    def test_wallust_installed(self):
        """Detect if wallust is installed."""
        with patch("shutil.which", return_value="/usr/bin/wallust"):
            assert WallustLoader.is_installed() is True

    def test_wallust_not_installed(self):
        """Return False when wallust not installed."""
        with patch("shutil.which", return_value=None):
            assert WallustLoader.is_installed() is False

    def test_find_config_dir_xdg(self):
        """Find Wallust config directory from XDG_CONFIG_HOME."""
        with tempfile.TemporaryDirectory() as tmpdir:
            wallust_dir = Path(tmpdir) / "wallust"
            wallust_dir.mkdir()

            with patch.dict(os.environ, {"XDG_CONFIG_HOME": tmpdir}):
                result = WallustLoader.find_config_dir()
                assert result == wallust_dir

    def test_find_config_dir_home_fallback(self):
        """Find Wallust config directory from ~/.config fallback."""
        with tempfile.TemporaryDirectory() as tmpdir:
            home_config = Path(tmpdir) / ".config" / "wallust"
            home_config.mkdir(parents=True)

            with patch.dict(os.environ, {"XDG_CONFIG_HOME": ""}, clear=True):
                with patch("pathlib.Path.home", return_value=Path(tmpdir)):
                    result = WallustLoader.find_config_dir()
                    assert result == home_config

    def test_find_config_dir_not_found(self):
        """Return None when config directory not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": ""}, clear=True):
                with patch("pathlib.Path.home", return_value=Path(tmpdir)):
                    result = WallustLoader.find_config_dir()
                    assert result is None


class TestColorParsing:
    """Test parsing various color file formats."""

    def test_parse_hypr_colors_conf(self):
        """Parse Hyprland colors.conf format."""
        sample_conf = """
        $color0 = rgb(1e1e2e)
        $color1 = rgb(f38ba8)
        $color2 = rgb(a6e3a1)
        $accent = rgb(89b4fa)
        $background = rgb(1e1e2e)
        $foreground = rgb(cdd6f4)
        """
        colors = WallustLoader._parse_hypr_colors(sample_conf)
        assert colors["color0"] == "#1e1e2e"
        assert colors["color1"] == "#f38ba8"
        assert colors["color2"] == "#a6e3a1"
        assert colors["accent"] == "#89b4fa"
        assert colors["background"] == "#1e1e2e"
        assert colors["foreground"] == "#cdd6f4"

    def test_parse_hypr_colors_empty(self):
        """Parse empty Hyprland colors.conf."""
        colors = WallustLoader._parse_hypr_colors("")
        assert colors == {}

    def test_parse_hypr_colors_malformed(self):
        """Parse malformed Hyprland colors.conf gracefully."""
        sample_conf = """
        # This is a comment
        $color0 = invalid
        some random text
        $color1 = rgb(f38ba8)
        """
        colors = WallustLoader._parse_hypr_colors(sample_conf)
        # Should only get the valid one
        assert "color1" in colors
        assert colors["color1"] == "#f38ba8"
        assert "color0" not in colors

    def test_parse_css_colors(self):
        """Parse CSS custom properties."""
        sample_css = """
        :root {
            --color0: #1e1e2e;
            --color1: #f38ba8;
            --accent: #89b4fa;
            --background: #1e1e2e;
        }
        """
        colors = WallustLoader._parse_css_colors(sample_css)
        assert colors["color0"] == "#1e1e2e"
        assert colors["color1"] == "#f38ba8"
        assert colors["accent"] == "#89b4fa"
        assert colors["background"] == "#1e1e2e"

    def test_parse_css_colors_empty(self):
        """Parse empty CSS file."""
        colors = WallustLoader._parse_css_colors("")
        assert colors == {}

    def test_parse_css_colors_malformed(self):
        """Parse malformed CSS gracefully."""
        sample_css = """
        :root {
            --color0: invalid;
            --color1: #f38ba8;
            some random text
        }
        """
        colors = WallustLoader._parse_css_colors(sample_css)
        # Should only get the valid one
        assert "color1" in colors
        assert colors["color1"] == "#f38ba8"
        assert "color0" not in colors


class TestColorPalette:
    """Test ColorPalette data structure."""

    def test_color_palette_creation(self):
        """Create color palette with standard colors."""
        palette = ColorPalette(
            background="#1e1e2e",
            foreground="#cdd6f4",
            accent="#89b4fa",
            color0="#1e1e2e",
            color1="#f38ba8",
        )
        assert palette.background == "#1e1e2e"
        assert palette.foreground == "#cdd6f4"
        assert palette.accent == "#89b4fa"
        assert palette.color0 == "#1e1e2e"
        assert palette.color1 == "#f38ba8"

    def test_color_palette_minimal(self):
        """Create minimal color palette with only required colors."""
        palette = ColorPalette(
            background="#000000",
            foreground="#ffffff",
            accent="#0000ff",
        )
        assert palette.background == "#000000"
        assert palette.foreground == "#ffffff"
        assert palette.accent == "#0000ff"
        assert palette.color0 is None
        assert palette.color15 is None

    def test_to_css(self):
        """Convert palette to CSS custom properties."""
        palette = ColorPalette(
            background="#1e1e2e",
            foreground="#cdd6f4",
            accent="#89b4fa",
            color0="#1e1e2e",
            color1="#f38ba8",
        )
        css = palette.to_css()
        assert ":root {" in css
        assert "--background: #1e1e2e;" in css
        assert "--foreground: #cdd6f4;" in css
        assert "--accent: #89b4fa;" in css
        assert "--color0: #1e1e2e;" in css
        assert "--color1: #f38ba8;" in css
        assert "}" in css

    def test_to_css_minimal(self):
        """Convert minimal palette to CSS."""
        palette = ColorPalette(
            background="#000000",
            foreground="#ffffff",
            accent="#0000ff",
        )
        css = palette.to_css()
        assert "--background: #000000;" in css
        assert "--foreground: #ffffff;" in css
        assert "--accent: #0000ff;" in css
        # Should not contain undefined colors
        assert "--color0:" not in css

    def test_to_dict(self):
        """Convert palette to dictionary for easy access."""
        palette = ColorPalette(
            background="#1e1e2e",
            foreground="#cdd6f4",
            accent="#89b4fa",
            color0="#1e1e2e",
            color1="#f38ba8",
        )
        result = palette.to_dict()
        assert result["background"] == "#1e1e2e"
        assert result["foreground"] == "#cdd6f4"
        assert result["accent"] == "#89b4fa"
        assert result["color0"] == "#1e1e2e"
        assert result["color1"] == "#f38ba8"
        assert "color2" not in result  # Not set


class TestWallustLoader:
    """Test WallustLoader class."""

    def test_load_colors_from_hypr(self):
        """Load colors from Hyprland colors.conf."""
        hypr_content = """
        $background = rgb(1e1e2e)
        $foreground = rgb(cdd6f4)
        $accent = rgb(89b4fa)
        $color0 = rgb(1e1e2e)
        $color1 = rgb(f38ba8)
        """

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create fake Hyprland config
            hypr_dir = Path(tmpdir) / ".config" / "hypr" / "config"
            hypr_dir.mkdir(parents=True)
            colors_file = hypr_dir / "colors.conf"
            colors_file.write_text(hypr_content)

            # Create fake wallust config dir
            wallust_dir = Path(tmpdir) / ".config" / "wallust"
            wallust_dir.mkdir(parents=True)

            with patch("pathlib.Path.home", return_value=Path(tmpdir)):
                with patch.dict(os.environ, {"XDG_CONFIG_HOME": ""}, clear=True):
                    palette = WallustLoader.load_colors()

                    assert palette is not None
                    assert palette.background == "#1e1e2e"
                    assert palette.foreground == "#cdd6f4"
                    assert palette.accent == "#89b4fa"
                    assert palette.color0 == "#1e1e2e"
                    assert palette.color1 == "#f38ba8"

    def test_load_colors_fallback_to_css(self):
        """Try CSS if Hyprland colors.conf not available."""
        css_content = """
        :root {
            --background: #1e1e2e;
            --foreground: #cdd6f4;
            --accent: #89b4fa;
            --color0: #1e1e2e;
            --color1: #f38ba8;
        }
        """

        with tempfile.TemporaryDirectory() as tmpdir:
            # No Hyprland config, but create Waybar CSS
            waybar_dir = Path(tmpdir) / ".config" / "waybar"
            waybar_dir.mkdir(parents=True)
            colors_file = waybar_dir / "colors.css"
            colors_file.write_text(css_content)

            # Create fake wallust config dir
            wallust_dir = Path(tmpdir) / ".config" / "wallust"
            wallust_dir.mkdir(parents=True)

            with patch("pathlib.Path.home", return_value=Path(tmpdir)):
                with patch.dict(os.environ, {"XDG_CONFIG_HOME": ""}, clear=True):
                    palette = WallustLoader.load_colors()

                    assert palette is not None
                    assert palette.background == "#1e1e2e"
                    assert palette.foreground == "#cdd6f4"
                    assert palette.accent == "#89b4fa"

    def test_load_colors_no_config_found(self):
        """Return None when no config directory found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("pathlib.Path.home", return_value=Path(tmpdir)):
                with patch.dict(os.environ, {"XDG_CONFIG_HOME": ""}, clear=True):
                    palette = WallustLoader.load_colors()
                    assert palette is None

    def test_load_colors_no_color_files(self):
        """Return None when config dir exists but no color files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create wallust config dir but no color files
            wallust_dir = Path(tmpdir) / ".config" / "wallust"
            wallust_dir.mkdir(parents=True)

            with patch("pathlib.Path.home", return_value=Path(tmpdir)):
                with patch.dict(os.environ, {"XDG_CONFIG_HOME": ""}, clear=True):
                    palette = WallustLoader.load_colors()
                    assert palette is None

    def test_colors_to_palette_basic(self):
        """Convert colors dict to ColorPalette."""
        colors = {
            "background": "#1e1e2e",
            "foreground": "#cdd6f4",
            "accent": "#89b4fa",
            "color0": "#1e1e2e",
            "color1": "#f38ba8",
        }

        palette = WallustLoader._colors_to_palette(colors)

        assert palette.background == "#1e1e2e"
        assert palette.foreground == "#cdd6f4"
        assert palette.accent == "#89b4fa"
        assert palette.color0 == "#1e1e2e"
        assert palette.color1 == "#f38ba8"

    def test_colors_to_palette_with_defaults(self):
        """Convert colors dict with fallback defaults."""
        colors = {
            "color0": "#000000",
            "color4": "#0000ff",
            "color7": "#ffffff",
        }

        palette = WallustLoader._colors_to_palette(colors)

        # Should use color0 as background fallback
        assert palette.background == "#000000"
        # Should use color7 as foreground fallback
        assert palette.foreground == "#ffffff"
        # Should use color4 as accent fallback
        assert palette.accent == "#0000ff"

    def test_colors_to_palette_all_16_colors(self):
        """Convert all 16 terminal colors."""
        colors = {f"color{i}": f"#{i:02x}{i:02x}{i:02x}" for i in range(16)}
        colors.update({
            "background": "#000000",
            "foreground": "#ffffff",
            "accent": "#0000ff",
        })

        palette = WallustLoader._colors_to_palette(colors)

        for i in range(16):
            color_attr = getattr(palette, f"color{i}")
            assert color_attr == f"#{i:02x}{i:02x}{i:02x}"
