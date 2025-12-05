"""Main exporter class for generating keybinding cheatsheets."""

from pathlib import Path
from datetime import datetime
from typing import Optional

from hyprbind.core.models import Config
from hyprbind.export.markdown_generator import MarkdownGenerator
from hyprbind.export.html_generator import HTMLGenerator
from hyprbind.export.pdf_generator import PDFGenerator


class Exporter:
    """Export keybindings to various formats."""

    def __init__(self, config: Config) -> None:
        """
        Initialize exporter with configuration.

        Args:
            config: Hyprland configuration with keybindings
        """
        self.config = config
        self.markdown_gen = MarkdownGenerator(config)
        self.html_gen = HTMLGenerator(config)
        self.pdf_gen = PDFGenerator(config)

    def export_markdown(self, output_path: Path) -> None:
        """
        Export keybindings to Markdown format.

        Args:
            output_path: Path where to save the Markdown file

        Raises:
            PermissionError: If output path is not writable
        """
        content = self._generate_markdown()
        output_path.write_text(content)

    def export_html(self, output_path: Path) -> None:
        """
        Export keybindings to HTML format.

        Args:
            output_path: Path where to save the HTML file

        Raises:
            PermissionError: If output path is not writable
        """
        content = self._generate_html()
        output_path.write_text(content)

    def export_pdf(self, output_path: Path) -> None:
        """
        Export keybindings to PDF format.

        Args:
            output_path: Path where to save the PDF file

        Raises:
            PermissionError: If output path is not writable
            Exception: If PDF generation fails
        """
        content = self._generate_pdf()
        output_path.write_bytes(content)

    def _generate_markdown(self) -> str:
        """
        Generate Markdown content.

        Returns:
            Markdown formatted string
        """
        return self.markdown_gen.generate()

    def _generate_html(self) -> str:
        """
        Generate HTML content.

        Returns:
            HTML formatted string
        """
        return self.html_gen.generate()

    def _generate_pdf(self) -> bytes:
        """
        Generate PDF content.

        Returns:
            PDF as bytes

        Raises:
            Exception: If PDF generation is not available
        """
        return self.pdf_gen.generate()
