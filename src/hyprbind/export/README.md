# Export Module

The export module provides functionality to generate keybinding cheatsheets in multiple formats: Markdown, HTML, and PDF.

## Features

- **Markdown Export**: Clean, readable Markdown format with category grouping
- **HTML Export**: Styled HTML with embedded CSS, print-friendly, and responsive
- **PDF Export**: Professional PDF documents generated from HTML (requires weasyprint)

## Usage

### Programmatic Usage

```python
from pathlib import Path
from hyprbind.core.models import Config
from hyprbind.export.exporter import Exporter

# Load your config
config = Config()
# ... add bindings to config ...

# Create exporter
exporter = Exporter(config)

# Export to different formats
exporter.export_markdown(Path("keybindings.md"))
exporter.export_html(Path("keybindings.html"))
exporter.export_pdf(Path("keybindings.pdf"))  # Requires weasyprint
```

### GUI Usage

1. Open HyprBind application
2. Navigate to the **Cheatsheet** tab
3. Click one of the export buttons:
   - **PDF** - Export to PDF format
   - **HTML** - Export to HTML format
   - **Markdown** - Export to Markdown format
4. Choose save location in the file dialog
5. Click **Save**

## Output Examples

### Markdown Format

```markdown
# Hyprland Keybindings

**Generated:** 2025-11-13 12:00:00
**Config:** `/home/user/.config/hypr/config/keybinds.conf`

## Window Actions

- `Super + Q` - Close window (killactive)
- `Super + F` - Fullscreen (fullscreen)

## Applications

- `Super + T` - Terminal (exec, alacritty)
- `Super + Shift + B` - Browser (exec, firefox)
```

### HTML Format

The HTML export includes:
- Responsive design with mobile support
- Professional styling with embedded CSS
- Categorized tables for easy navigation
- Print-friendly layout
- Metadata footer with generation date and config path

### PDF Format

The PDF export provides:
- Professional document layout
- Print-ready formatting
- All content from HTML version
- Proper page breaks for categories

## Dependencies

### Required (always available)
- No additional dependencies for Markdown and HTML export

### Optional (for PDF export)
- `weasyprint>=60.0` - HTML to PDF conversion

Install PDF support:
```bash
pip install hyprbind[pdf]
# or
pip install weasyprint
```

## Architecture

The export module is organized into specialized generators:

- `exporter.py` - Main `Exporter` class that orchestrates export operations
- `markdown_generator.py` - Generates Markdown formatted output
- `html_generator.py` - Generates HTML with embedded CSS
- `pdf_generator.py` - Converts HTML to PDF using weasyprint

## Features

### Metadata Inclusion
All exports include:
- Generation timestamp
- Source configuration file path

### Category Grouping
Bindings are automatically grouped by category and sorted alphabetically.

### Special Character Handling
- **HTML**: Proper escaping of HTML entities (`<`, `>`, `&`, etc.)
- **Markdown**: Preserves markdown formatting in descriptions

### Error Handling
- Permission errors for read-only directories
- Missing dependency warnings (especially for PDF)
- User cancellation support

## Testing

The export module has comprehensive test coverage (19 tests):

```bash
pytest tests/export/
```

Test coverage includes:
- Markdown generation and file writing
- HTML generation with CSS and tables
- PDF generation (mocked weasyprint)
- Edge cases (empty configs, permissions)
- Metadata inclusion
- Category grouping
- Special character handling
