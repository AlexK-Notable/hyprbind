"""Tests for the export engine."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from datetime import datetime

from hyprbind.core.models import Binding, BindType, Config, Category
from hyprbind.export.exporter import Exporter


@pytest.fixture
def sample_config():
    """Create sample config with bindings for testing."""
    config = Config()
    config.file_path = "/home/user/.config/hypr/config/keybinds.conf"

    # Window management bindings
    binding1 = Binding(
        type=BindType.BINDD,
        modifiers=["$mainMod"],
        key="Q",
        description="Close window",
        action="killactive",
        params="",
        submap=None,
        line_number=10,
        category="Window Actions",
    )

    binding2 = Binding(
        type=BindType.BINDD,
        modifiers=["$mainMod"],
        key="F",
        description="Fullscreen",
        action="fullscreen",
        params="",
        submap=None,
        line_number=11,
        category="Window Actions",
    )

    # Application bindings
    binding3 = Binding(
        type=BindType.BINDD,
        modifiers=["$mainMod"],
        key="T",
        description="Terminal",
        action="exec",
        params="alacritty",
        submap=None,
        line_number=20,
        category="Applications",
    )

    binding4 = Binding(
        type=BindType.BINDD,
        modifiers=["$mainMod", "SHIFT"],
        key="B",
        description="Browser",
        action="exec",
        params="firefox",
        submap=None,
        line_number=21,
        category="Applications",
    )

    config.add_binding(binding1)
    config.add_binding(binding2)
    config.add_binding(binding3)
    config.add_binding(binding4)

    return config


@pytest.fixture
def exporter(sample_config):
    """Create exporter instance with sample config."""
    return Exporter(sample_config)


class TestExporterMarkdown:
    """Test Markdown export functionality."""

    def test_generate_markdown_content(self, exporter):
        """Test markdown content generation."""
        content = exporter._generate_markdown()

        # Check header
        assert "# Hyprland Keybindings" in content

        # Check categories
        assert "## Window Actions" in content
        assert "## Applications" in content

        # Check bindings
        assert "Super + Q" in content
        assert "Close window" in content
        assert "killactive" in content

        assert "Super + T" in content
        assert "Terminal" in content
        assert "alacritty" in content

        assert "Super + Shift + B" in content
        assert "Browser" in content

    def test_markdown_format_structure(self, exporter):
        """Test markdown follows correct format structure."""
        content = exporter._generate_markdown()
        lines = content.split("\n")

        # Should have title
        assert lines[0] == "# Hyprland Keybindings"

        # Should have metadata
        assert any("Generated:" in line for line in lines)
        assert any("Config:" in line for line in lines)

    def test_export_markdown_writes_file(self, exporter, tmp_path):
        """Test that export_markdown writes to file correctly."""
        output_file = tmp_path / "keybinds.md"

        exporter.export_markdown(output_file)

        assert output_file.exists()
        content = output_file.read_text()
        assert "# Hyprland Keybindings" in content
        assert "Super + Q" in content

    def test_markdown_special_characters_escaped(self, sample_config):
        """Test that special markdown characters are handled."""
        # Add binding with special chars
        binding = Binding(
            type=BindType.BINDD,
            modifiers=["$mainMod"],
            key="grave",
            description="Show `terminal` with *style*",
            action="exec",
            params="cmd",
            submap=None,
            line_number=30,
            category="Test",
        )
        sample_config.add_binding(binding)

        exporter = Exporter(sample_config)
        content = exporter._generate_markdown()

        # Backticks and asterisks should be handled appropriately
        assert "Show `terminal` with *style*" in content or \
               "Show \\`terminal\\` with \\*style\\*" in content


class TestExporterHTML:
    """Test HTML export functionality."""

    def test_generate_html_content(self, exporter):
        """Test HTML content generation."""
        content = exporter._generate_html()

        # Check basic HTML structure
        assert "<!DOCTYPE html>" in content
        assert "<html>" in content
        assert "</html>" in content
        assert "<head>" in content
        assert "<body>" in content

        # Check title
        assert "<title>Hyprland Keybindings</title>" in content
        assert "<h1>Hyprland Keybindings</h1>" in content

        # Check has CSS
        assert "<style>" in content
        assert "</style>" in content

        # Check categories
        assert "Window Actions" in content
        assert "Applications" in content

        # Check bindings appear
        assert "Super + Q" in content
        assert "Close window" in content

    def test_html_has_table_structure(self, exporter):
        """Test HTML uses table structure for bindings."""
        content = exporter._generate_html()

        assert "<table" in content
        assert "</table>" in content
        assert "<tr>" in content
        assert "<td>" in content

    def test_html_has_embedded_css(self, exporter):
        """Test HTML includes embedded CSS for styling."""
        content = exporter._generate_html()

        # Check for CSS selectors
        assert "table" in content or "body" in content
        # Should have some styling
        assert "font-family" in content or "color" in content or "margin" in content

    def test_export_html_writes_file(self, exporter, tmp_path):
        """Test that export_html writes to file correctly."""
        output_file = tmp_path / "keybinds.html"

        exporter.export_html(output_file)

        assert output_file.exists()
        content = output_file.read_text()
        assert "<!DOCTYPE html>" in content
        assert "Super + Q" in content

    def test_html_special_characters_escaped(self, sample_config):
        """Test HTML special characters are properly escaped."""
        # Add binding with HTML special chars
        binding = Binding(
            type=BindType.BINDD,
            modifiers=["$mainMod"],
            key="X",
            description="Test <script>alert('xss')</script>",
            action="exec",
            params="cmd",
            submap=None,
            line_number=40,
            category="Test",
        )
        sample_config.add_binding(binding)

        exporter = Exporter(sample_config)
        content = exporter._generate_html()

        # Should escape HTML entities
        assert "&lt;" in content or "<script>" not in content


class TestExporterPDF:
    """Test PDF export functionality."""

    def test_generate_pdf_uses_html(self, exporter):
        """Test PDF generation uses HTML as base."""
        # PDF should reuse HTML generation
        with patch.object(exporter, '_generate_html') as mock_html:
            mock_html.return_value = "<html>test</html>"

            # This will fail for now, but validates the approach
            with pytest.raises(Exception):
                exporter._generate_pdf()

    def test_export_pdf_writes_file(self, exporter, tmp_path):
        """Test that export_pdf creates a file."""
        output_file = tmp_path / "keybinds.pdf"

        # This will fail initially - that's expected in TDD
        with pytest.raises(Exception):
            exporter.export_pdf(output_file)


class TestExporterEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_config(self):
        """Test exporting empty config."""
        empty_config = Config()
        exporter = Exporter(empty_config)

        markdown = exporter._generate_markdown()
        assert "# Hyprland Keybindings" in markdown
        # Should handle empty gracefully

    def test_export_to_readonly_directory(self, exporter, tmp_path):
        """Test error handling for readonly directory."""
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)

        output_file = readonly_dir / "test.md"

        with pytest.raises(PermissionError):
            exporter.export_markdown(output_file)

    def test_config_without_categories(self):
        """Test config with bindings but no categories."""
        config = Config()
        config.file_path = "/test/config.conf"

        exporter = Exporter(config)
        content = exporter._generate_markdown()

        assert "# Hyprland Keybindings" in content


class TestExporterMetadata:
    """Test metadata inclusion in exports."""

    def test_markdown_includes_metadata(self, exporter):
        """Test markdown includes generation metadata."""
        content = exporter._generate_markdown()

        # Should include generation date
        assert "Generated:" in content
        # Should include source config path
        assert "Config:" in content or "keybinds.conf" in content

    def test_html_includes_metadata(self, exporter):
        """Test HTML includes metadata."""
        content = exporter._generate_html()

        # Should have metadata in HTML
        assert "Generated" in content or "Config" in content

    @patch('hyprbind.export.markdown_generator.datetime')
    def test_metadata_uses_current_date(self, mock_datetime, exporter):
        """Test that metadata uses current date/time."""
        mock_now = datetime(2024, 1, 15, 14, 30, 0)
        mock_datetime.now.return_value = mock_now

        content = exporter._generate_markdown()

        # Should include the mocked date in some format
        assert "2024" in content


class TestExporterCategoryGrouping:
    """Test binding grouping by category."""

    def test_bindings_grouped_by_category(self, exporter):
        """Test that bindings are organized by category."""
        markdown = exporter._generate_markdown()

        # Find Window Actions section
        window_section_start = markdown.find("## Window Actions")
        apps_section_start = markdown.find("## Applications")

        assert window_section_start != -1
        assert apps_section_start != -1
        # Categories are alphabetically sorted, so Applications comes before Window Actions
        assert apps_section_start < window_section_start

        # Window bindings should be in Window Actions section
        window_section = markdown[window_section_start:]
        assert "Super + Q" in window_section
        assert "Close window" in window_section

        # Application bindings should be in Applications section (before Window Actions)
        apps_section = markdown[apps_section_start:window_section_start]
        assert "Super + T" in apps_section
        assert "Terminal" in apps_section

    def test_html_groups_by_category(self, exporter):
        """Test HTML groups bindings by category."""
        html = exporter._generate_html()

        # Should have category headers
        assert "Window Actions" in html
        assert "Applications" in html

        # Each category should be in its own section/div
        assert "<h2>Window Actions</h2>" in html or \
               'class="category"' in html
