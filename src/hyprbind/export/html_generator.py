"""HTML generator for keybinding cheatsheets."""

from datetime import datetime
from html import escape
from typing import List

from hyprbind.core.models import Config, Binding


class HTMLGenerator:
    """Generate HTML formatted keybinding cheatsheets."""

    def __init__(self, config: Config) -> None:
        """
        Initialize HTML generator.

        Args:
            config: Hyprland configuration with keybindings
        """
        self.config = config

    def generate(self) -> str:
        """
        Generate complete HTML document.

        Returns:
            HTML formatted string
        """
        parts = []

        # HTML header
        parts.append("<!DOCTYPE html>")
        parts.append("<html>")
        parts.append("<head>")
        parts.append("    <meta charset=\"UTF-8\">")
        parts.append("    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">")
        parts.append("    <title>Hyprland Keybindings</title>")
        parts.append(self._generate_css())
        parts.append("</head>")
        parts.append("<body>")

        # Title and metadata
        parts.append("    <div class=\"container\">")
        parts.append("        <h1>Hyprland Keybindings</h1>")
        parts.append(self._generate_metadata_html())

        # Bindings by category
        categories = sorted(self.config.categories.keys())
        for category_name in categories:
            category = self.config.categories[category_name]
            if category.bindings:
                parts.append(f"        <div class=\"category\">")
                parts.append(f"            <h2>{escape(category_name)}</h2>")
                parts.append(self._generate_table(category.bindings))
                parts.append("        </div>")

        parts.append("    </div>")
        parts.append("</body>")
        parts.append("</html>")

        return "\n".join(parts)

    def _generate_css(self) -> str:
        """
        Generate embedded CSS styles.

        Returns:
            CSS style block
        """
        return """    <style>
        * {
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
                         'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }

        h2 {
            color: #34495e;
            margin-top: 30px;
            margin-bottom: 15px;
            border-left: 4px solid #3498db;
            padding-left: 15px;
        }

        .metadata {
            background: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 25px;
            font-size: 0.9em;
        }

        .metadata p {
            margin: 5px 0;
        }

        .category {
            margin-bottom: 40px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            background: white;
        }

        thead {
            background: #3498db;
            color: white;
        }

        th {
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }

        td {
            padding: 12px;
            border-bottom: 1px solid #ecf0f1;
        }

        tr:hover {
            background: #f8f9fa;
        }

        .keybinding {
            font-family: 'Courier New', monospace;
            background: #e8f4f8;
            padding: 4px 8px;
            border-radius: 3px;
            font-weight: 600;
            color: #2c3e50;
            white-space: nowrap;
        }

        .action {
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            color: #7f8c8d;
        }

        @media print {
            body {
                background: white;
            }
            .container {
                box-shadow: none;
            }
            tr {
                page-break-inside: avoid;
            }
        }
    </style>"""

    def _generate_metadata_html(self) -> str:
        """
        Generate HTML metadata section.

        Returns:
            HTML metadata block
        """
        now = datetime.now()
        lines = []
        lines.append("        <div class=\"metadata\">")
        lines.append(f"            <p><strong>Generated:</strong> {now.strftime('%Y-%m-%d %H:%M:%S')}</p>")

        if self.config.file_path:
            lines.append(f"            <p><strong>Config:</strong> <code>{escape(self.config.file_path)}</code></p>")

        lines.append("        </div>")
        return "\n".join(lines)

    def _generate_table(self, bindings: List[Binding]) -> str:
        """
        Generate HTML table for bindings.

        Args:
            bindings: List of bindings to include in table

        Returns:
            HTML table string
        """
        lines = []
        lines.append("            <table>")
        lines.append("                <thead>")
        lines.append("                    <tr>")
        lines.append("                        <th>Keybinding</th>")
        lines.append("                        <th>Description</th>")
        lines.append("                        <th>Action</th>")
        lines.append("                    </tr>")
        lines.append("                </thead>")
        lines.append("                <tbody>")

        for binding in bindings:
            key_combo = escape(binding.display_name)
            desc = escape(binding.description or "No description")
            action = escape(binding.action)
            params = escape(binding.params) if binding.params else ""
            action_full = f"{action}, {params}" if params else action

            lines.append("                    <tr>")
            lines.append(f"                        <td><span class=\"keybinding\">{key_combo}</span></td>")
            lines.append(f"                        <td>{desc}</td>")
            lines.append(f"                        <td class=\"action\">{action_full}</td>")
            lines.append("                    </tr>")

        lines.append("                </tbody>")
        lines.append("            </table>")
        return "\n".join(lines)
