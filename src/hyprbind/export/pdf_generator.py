"""PDF generator for keybinding cheatsheets."""

from typing import Optional

from hyprbind.core.models import Config
from hyprbind.export.html_generator import HTMLGenerator


class PDFGenerator:
    """Generate PDF formatted keybinding cheatsheets."""

    def __init__(self, config: Config) -> None:
        """
        Initialize PDF generator.

        Args:
            config: Hyprland configuration with keybindings
        """
        self.config = config
        self.html_gen = HTMLGenerator(config)

    def generate(self) -> bytes:
        """
        Generate PDF document.

        Returns:
            PDF as bytes

        Raises:
            ImportError: If weasyprint is not available
            Exception: If PDF generation fails
        """
        try:
            from weasyprint import HTML
        except ImportError:
            raise ImportError(
                "weasyprint is required for PDF export. "
                "Install it with: pip install weasyprint"
            )

        # Generate HTML content
        html_content = self.html_gen.generate()

        # Convert HTML to PDF
        try:
            pdf_bytes = HTML(string=html_content).write_pdf()
            return pdf_bytes
        except Exception as e:
            raise Exception(f"PDF generation failed: {e}") from e
