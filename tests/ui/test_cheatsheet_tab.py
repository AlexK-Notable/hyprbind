"""Tests for cheatsheet tab."""

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk, Gio, GObject
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from hyprbind.ui.cheatsheet_tab import CheatsheetTab, BindingCardObject
from hyprbind.core.config_manager import ConfigManager
from hyprbind.core.models import Config, Category, Binding, BindType


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_config_path():
    """Path to sample keybinds config."""
    return Path(__file__).parent.parent / "fixtures" / "sample_keybinds.conf"


@pytest.fixture
def manager(sample_config_path):
    """ConfigManager with loaded config."""
    mgr = ConfigManager(sample_config_path, skip_validation=True)
    mgr.load()
    return mgr


@pytest.fixture
def empty_manager(tmp_path):
    """ConfigManager with empty config (isolated temp path)."""
    temp_config = tmp_path / "empty_keybinds.conf"
    temp_config.write_text("# Empty config\n")
    mgr = ConfigManager(temp_config, skip_validation=True)
    mgr.config = Config()
    return mgr


@pytest.fixture
def sample_binding():
    """Create a sample binding for testing."""
    return Binding(
        type=BindType.BINDD,
        modifiers=["$mainMod", "SHIFT"],
        key="Q",
        description="Close window",
        action="killactive",
        params="",
        submap=None,
        line_number=1,
        category="Window Management",
    )


# =============================================================================
# BindingCardObject Tests
# =============================================================================

class TestBindingCardObject:
    """Test BindingCardObject GObject wrapper."""

    def test_is_gobject(self, sample_binding):
        """BindingCardObject is a GObject."""
        obj = BindingCardObject(sample_binding)
        assert isinstance(obj, GObject.Object)

    def test_stores_binding(self, sample_binding):
        """BindingCardObject stores the binding."""
        obj = BindingCardObject(sample_binding)
        assert obj.binding is sample_binding

    def test_binding_property_accessible(self, sample_binding):
        """Binding property is accessible."""
        obj = BindingCardObject(sample_binding)
        assert obj.binding.key == "Q"
        assert obj.binding.description == "Close window"


# =============================================================================
# Basic Structure Tests
# =============================================================================

class TestCheatsheetTabStructure:
    """Test CheatsheetTab basic structure."""

    def test_cheatsheet_tab_is_box(self, manager):
        """Cheatsheet tab is a Gtk.Box."""
        tab = CheatsheetTab(manager)
        assert isinstance(tab, Gtk.Box)

    def test_has_grid_view(self, manager):
        """Tab has GridView widget."""
        tab = CheatsheetTab(manager)
        assert hasattr(tab, "grid_view")
        assert isinstance(tab.grid_view, Gtk.GridView)

    def test_has_list_store(self, manager):
        """Tab has Gio.ListStore."""
        tab = CheatsheetTab(manager)
        assert hasattr(tab, "list_store")
        assert isinstance(tab.list_store, Gio.ListStore)

    def test_has_selection_model(self, manager):
        """Tab has SingleSelection model."""
        tab = CheatsheetTab(manager)
        assert hasattr(tab, "selection_model")
        assert isinstance(tab.selection_model, Gtk.SingleSelection)

    def test_stores_config_manager(self, manager):
        """Tab stores config_manager reference."""
        tab = CheatsheetTab(manager)
        assert tab.config_manager is manager


# =============================================================================
# Toolbar Tests
# =============================================================================

class TestToolbar:
    """Test toolbar with export buttons."""

    def test_has_pdf_button(self, manager):
        """Tab has PDF export button."""
        tab = CheatsheetTab(manager)
        assert hasattr(tab, "export_pdf_btn")
        assert isinstance(tab.export_pdf_btn, Gtk.Button)

    def test_has_html_button(self, manager):
        """Tab has HTML export button."""
        tab = CheatsheetTab(manager)
        assert hasattr(tab, "export_html_btn")
        assert isinstance(tab.export_html_btn, Gtk.Button)

    def test_has_markdown_button(self, manager):
        """Tab has Markdown export button."""
        tab = CheatsheetTab(manager)
        assert hasattr(tab, "export_md_btn")
        assert isinstance(tab.export_md_btn, Gtk.Button)

    def test_pdf_button_has_tooltip(self, manager):
        """PDF button has tooltip."""
        tab = CheatsheetTab(manager)
        assert tab.export_pdf_btn.get_tooltip_text() is not None

    def test_html_button_has_tooltip(self, manager):
        """HTML button has tooltip."""
        tab = CheatsheetTab(manager)
        assert tab.export_html_btn.get_tooltip_text() is not None

    def test_markdown_button_has_tooltip(self, manager):
        """Markdown button has tooltip."""
        tab = CheatsheetTab(manager)
        assert tab.export_md_btn.get_tooltip_text() is not None


# =============================================================================
# Grid View Configuration Tests
# =============================================================================

class TestGridViewConfig:
    """Test GridView configuration."""

    def test_grid_has_max_columns(self, manager):
        """GridView has max columns set."""
        tab = CheatsheetTab(manager)
        assert tab.grid_view.get_max_columns() == 3

    def test_grid_has_min_columns(self, manager):
        """GridView has min columns set."""
        tab = CheatsheetTab(manager)
        assert tab.grid_view.get_min_columns() == 1


# =============================================================================
# Data Loading Tests
# =============================================================================

class TestDataLoading:
    """Test binding data loading."""

    def test_loads_bindings_on_init(self, manager):
        """Tab loads bindings on initialization."""
        tab = CheatsheetTab(manager)
        # Should have items if config has bindings
        if manager.config and manager.config.get_all_bindings():
            assert tab.list_store.get_n_items() > 0

    def test_empty_config_shows_no_items(self, empty_manager):
        """Empty config shows no items."""
        tab = CheatsheetTab(empty_manager)
        assert tab.list_store.get_n_items() == 0

    def test_list_store_items_are_binding_card_objects(self, manager):
        """List store contains BindingCardObject instances."""
        tab = CheatsheetTab(manager)
        if tab.list_store.get_n_items() > 0:
            item = tab.list_store.get_item(0)
            assert isinstance(item, BindingCardObject)

    def test_binding_count_matches_config(self, manager):
        """Number of items matches config binding count."""
        tab = CheatsheetTab(manager)
        expected_count = len(manager.config.get_all_bindings()) if manager.config else 0
        assert tab.list_store.get_n_items() == expected_count


# =============================================================================
# Observer Pattern Tests
# =============================================================================

class TestObserverPattern:
    """Test observer registration and reload."""

    def test_registers_as_observer(self, manager):
        """Tab registers itself with config manager."""
        initial_count = len(manager._observers)
        tab = CheatsheetTab(manager)
        assert len(manager._observers) == initial_count + 1

    def test_reload_cheatsheet_method_exists(self, manager):
        """Tab has reload_cheatsheet method."""
        tab = CheatsheetTab(manager)
        assert hasattr(tab, "reload_cheatsheet")
        assert callable(tab.reload_cheatsheet)

    def test_reload_clears_and_repopulates(self, manager):
        """Reload clears list and repopulates from config."""
        tab = CheatsheetTab(manager)
        initial_count = tab.list_store.get_n_items()

        # Clear manually
        tab.list_store.remove_all()
        assert tab.list_store.get_n_items() == 0

        # Reload should restore
        tab.reload_cheatsheet()
        assert tab.list_store.get_n_items() == initial_count


# =============================================================================
# Export Button Handler Tests
# =============================================================================

class TestExportHandlers:
    """Test export button click handlers."""

    def test_pdf_export_calls_show_dialog(self, manager):
        """PDF export calls _show_export_dialog."""
        tab = CheatsheetTab(manager)

        with patch.object(tab, "_show_export_dialog") as mock_dialog:
            tab._on_export_pdf(tab.export_pdf_btn)
            mock_dialog.assert_called_once_with("pdf", "PDF Files", "*.pdf")

    def test_html_export_calls_show_dialog(self, manager):
        """HTML export calls _show_export_dialog."""
        tab = CheatsheetTab(manager)

        with patch.object(tab, "_show_export_dialog") as mock_dialog:
            tab._on_export_html(tab.export_html_btn)
            mock_dialog.assert_called_once_with("html", "HTML Files", "*.html")

    def test_markdown_export_calls_show_dialog(self, manager):
        """Markdown export calls _show_export_dialog."""
        tab = CheatsheetTab(manager)

        with patch.object(tab, "_show_export_dialog") as mock_dialog:
            tab._on_export_markdown(tab.export_md_btn)
            mock_dialog.assert_called_once_with("markdown", "Markdown Files", "*.md")


# =============================================================================
# Export Dialog Tests
# =============================================================================

class TestExportDialog:
    """Test export dialog behavior."""

    def test_export_with_no_config_shows_error(self, empty_manager):
        """Export without config shows error dialog."""
        tab = CheatsheetTab(empty_manager)
        tab.config_manager.config = None  # Force no config

        with patch.object(tab, "_show_error_dialog") as mock_error:
            tab._show_export_dialog("pdf", "PDF Files", "*.pdf")
            mock_error.assert_called_once()
            assert "No configuration" in mock_error.call_args[0][0]


# =============================================================================
# Export to File Tests
# =============================================================================

class TestExportToFile:
    """Test actual export functionality."""

    def test_export_pdf_calls_exporter(self, manager, tmp_path):
        """PDF export calls Exporter.export_pdf."""
        tab = CheatsheetTab(manager)
        output_path = tmp_path / "test.pdf"

        with patch("hyprbind.ui.cheatsheet_tab.Exporter") as MockExporter:
            mock_exporter = MagicMock()
            MockExporter.return_value = mock_exporter

            with patch.object(tab, "_show_success_dialog"):
                tab._export_to_file(output_path, "pdf")

            MockExporter.assert_called_once_with(manager.config)
            mock_exporter.export_pdf.assert_called_once_with(output_path)

    def test_export_html_calls_exporter(self, manager, tmp_path):
        """HTML export calls Exporter.export_html."""
        tab = CheatsheetTab(manager)
        output_path = tmp_path / "test.html"

        with patch("hyprbind.ui.cheatsheet_tab.Exporter") as MockExporter:
            mock_exporter = MagicMock()
            MockExporter.return_value = mock_exporter

            with patch.object(tab, "_show_success_dialog"):
                tab._export_to_file(output_path, "html")

            mock_exporter.export_html.assert_called_once_with(output_path)

    def test_export_markdown_calls_exporter(self, manager, tmp_path):
        """Markdown export calls Exporter.export_markdown."""
        tab = CheatsheetTab(manager)
        output_path = tmp_path / "test.md"

        with patch("hyprbind.ui.cheatsheet_tab.Exporter") as MockExporter:
            mock_exporter = MagicMock()
            MockExporter.return_value = mock_exporter

            with patch.object(tab, "_show_success_dialog"):
                tab._export_to_file(output_path, "markdown")

            mock_exporter.export_markdown.assert_called_once_with(output_path)

    def test_export_success_shows_dialog(self, manager, tmp_path):
        """Successful export shows success dialog."""
        tab = CheatsheetTab(manager)
        output_path = tmp_path / "test.md"

        with patch("hyprbind.ui.cheatsheet_tab.Exporter"):
            with patch.object(tab, "_show_success_dialog") as mock_success:
                tab._export_to_file(output_path, "markdown")
                mock_success.assert_called_once()
                assert "successful" in mock_success.call_args[0][0].lower()

    def test_export_error_shows_dialog(self, manager, tmp_path):
        """Export error shows error dialog."""
        tab = CheatsheetTab(manager)
        output_path = tmp_path / "test.pdf"

        with patch("hyprbind.ui.cheatsheet_tab.Exporter") as MockExporter:
            MockExporter.side_effect = Exception("Test error")

            with patch.object(tab, "_show_error_dialog") as mock_error:
                tab._export_to_file(output_path, "pdf")
                mock_error.assert_called_once()

    def test_import_error_shows_helpful_message(self, manager, tmp_path):
        """ImportError shows helpful message about dependencies."""
        tab = CheatsheetTab(manager)
        output_path = tmp_path / "test.pdf"

        with patch("hyprbind.ui.cheatsheet_tab.Exporter") as MockExporter:
            MockExporter.side_effect = ImportError("weasyprint")

            with patch.object(tab, "_show_error_dialog") as mock_error:
                tab._export_to_file(output_path, "pdf")
                mock_error.assert_called_once()
                # Should mention weasyprint
                assert "weasyprint" in mock_error.call_args[0][1].lower()


# =============================================================================
# Dialog Response Tests
# =============================================================================

class TestDialogResponse:
    """Test dialog response handling."""

    def test_dialog_cancel_does_not_export(self, manager):
        """Cancelled dialog does not export."""
        tab = CheatsheetTab(manager)

        mock_dialog = MagicMock()
        mock_result = MagicMock()
        mock_dialog.save_finish.side_effect = Exception("dismissed by user")

        with patch.object(tab, "_export_to_file") as mock_export:
            with patch.object(tab, "_show_error_dialog"):
                tab._on_export_dialog_response(mock_dialog, mock_result, "pdf")
                mock_export.assert_not_called()

    def test_dialog_success_exports(self, manager, tmp_path):
        """Successful dialog selection exports to file."""
        tab = CheatsheetTab(manager)
        output_path = tmp_path / "test.pdf"

        mock_dialog = MagicMock()
        mock_result = MagicMock()
        mock_file = MagicMock()
        mock_file.get_path.return_value = str(output_path)
        mock_dialog.save_finish.return_value = mock_file

        with patch.object(tab, "_export_to_file") as mock_export:
            tab._on_export_dialog_response(mock_dialog, mock_result, "pdf")
            mock_export.assert_called_once_with(output_path, "pdf")
