"""Load colors from Wallust dynamic theming system."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict
import shutil
import re
import os


@dataclass
class ColorPalette:
    """Standardized color palette."""

    background: str
    foreground: str
    accent: str
    color0: Optional[str] = None  # Black
    color1: Optional[str] = None  # Red
    color2: Optional[str] = None  # Green
    color3: Optional[str] = None  # Yellow
    color4: Optional[str] = None  # Blue
    color5: Optional[str] = None  # Magenta
    color6: Optional[str] = None  # Cyan
    color7: Optional[str] = None  # White
    color8: Optional[str] = None  # Bright black
    color9: Optional[str] = None  # Bright red
    color10: Optional[str] = None  # Bright green
    color11: Optional[str] = None  # Bright yellow
    color12: Optional[str] = None  # Bright blue
    color13: Optional[str] = None  # Bright magenta
    color14: Optional[str] = None  # Bright cyan
    color15: Optional[str] = None  # Bright white

    def to_css(self) -> str:
        """Convert palette to CSS custom properties."""
        lines = [":root {"]

        if self.background:
            lines.append(f"    --background: {self.background};")
        if self.foreground:
            lines.append(f"    --foreground: {self.foreground};")
        if self.accent:
            lines.append(f"    --accent: {self.accent};")

        for i in range(16):
            color = getattr(self, f"color{i}", None)
            if color:
                lines.append(f"    --color{i}: {color};")

        lines.append("}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for easy access."""
        result = {}
        if self.background:
            result["background"] = self.background
        if self.foreground:
            result["foreground"] = self.foreground
        if self.accent:
            result["accent"] = self.accent

        for i in range(16):
            color = getattr(self, f"color{i}", None)
            if color:
                result[f"color{i}"] = color

        return result


class WallustLoader:
    """Load colors from Wallust output files."""

    @staticmethod
    def is_installed() -> bool:
        """Check if Wallust is installed."""
        return shutil.which("wallust") is not None

    @staticmethod
    def find_config_dir() -> Optional[Path]:
        """Find Wallust config directory."""
        # Try XDG_CONFIG_HOME first
        xdg_config = os.getenv("XDG_CONFIG_HOME")
        if xdg_config:
            wallust_dir = Path(xdg_config) / "wallust"
            if wallust_dir.exists():
                return wallust_dir

        # Fallback to ~/.config/wallust
        home_config = Path.home() / ".config" / "wallust"
        if home_config.exists():
            return home_config

        return None

    @staticmethod
    def _parse_hypr_colors(content: str) -> Dict[str, str]:
        """Parse Hyprland colors.conf format.

        Example:
            $color0 = rgb(1e1e2e)
            $accent = rgb(89b4fa)
        """
        colors = {}
        # Pattern: $name = rgb(hex)
        pattern = r'\$(\w+)\s*=\s*rgb\(([0-9a-fA-F]{6})\)'

        for match in re.finditer(pattern, content):
            name, hex_value = match.groups()
            colors[name] = f"#{hex_value}"

        return colors

    @staticmethod
    def _parse_css_colors(content: str) -> Dict[str, str]:
        """Parse CSS custom properties.

        Example:
            --color0: #1e1e2e;
            --accent: #89b4fa;
        """
        colors = {}
        # Pattern: --name: #hex;
        pattern = r'--(\w+):\s*(#[0-9a-fA-F]{6});'

        for match in re.finditer(pattern, content):
            name, hex_value = match.groups()
            colors[name] = hex_value

        return colors

    @staticmethod
    def load_colors() -> Optional[ColorPalette]:
        """Load colors from Wallust output files.

        Tries multiple sources in order:
        1. Hyprland colors.conf
        2. Waybar colors.css
        3. Returns None if none available
        """
        config_dir = WallustLoader.find_config_dir()
        if not config_dir:
            return None

        # Try Hyprland colors first
        hypr_colors = Path.home() / ".config" / "hypr" / "config" / "colors.conf"
        if hypr_colors.exists():
            try:
                content = hypr_colors.read_text()
                colors = WallustLoader._parse_hypr_colors(content)
                return WallustLoader._colors_to_palette(colors)
            except Exception:
                pass

        # Try Waybar colors as fallback
        waybar_colors = Path.home() / ".config" / "waybar" / "colors.css"
        if waybar_colors.exists():
            try:
                content = waybar_colors.read_text()
                colors = WallustLoader._parse_css_colors(content)
                return WallustLoader._colors_to_palette(colors)
            except Exception:
                pass

        return None

    @staticmethod
    def _colors_to_palette(colors: Dict[str, str]) -> ColorPalette:
        """Convert parsed colors dict to ColorPalette."""
        return ColorPalette(
            background=colors.get("background", colors.get("color0", "#000000")),
            foreground=colors.get("foreground", colors.get("color7", "#ffffff")),
            accent=colors.get("accent", colors.get("color4", "#0000ff")),
            color0=colors.get("color0"),
            color1=colors.get("color1"),
            color2=colors.get("color2"),
            color3=colors.get("color3"),
            color4=colors.get("color4"),
            color5=colors.get("color5"),
            color6=colors.get("color6"),
            color7=colors.get("color7"),
            color8=colors.get("color8"),
            color9=colors.get("color9"),
            color10=colors.get("color10"),
            color11=colors.get("color11"),
            color12=colors.get("color12"),
            color13=colors.get("color13"),
            color14=colors.get("color14"),
            color15=colors.get("color15"),
        )
