"""Test application lifecycle manager."""
import pytest
from tests.e2e.app_lifecycle import setup_headless_display, ApplicationContext


def test_setup_headless_display():
    """Test headless display configuration."""
    setup_headless_display()

    import os
    assert 'GDK_BACKEND' in os.environ
    assert os.environ['GDK_BACKEND'] == 'broadway'


def test_application_context_manager():
    """Test application context manager lifecycle."""
    from pathlib import Path
    import tempfile

    with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
        f.write("# Test config\n")
        config_path = Path(f.name)

    try:
        with ApplicationContext(config_path) as (app, window):
            assert app is not None
            assert window is not None
            assert window.config_manager.config_path == config_path
    finally:
        config_path.unlink()
