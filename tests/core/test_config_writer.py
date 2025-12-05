import pytest
from pathlib import Path
import tempfile

from hyprbind.core.config_writer import ConfigWriter
from hyprbind.core.models import Config, Binding, BindType


@pytest.fixture
def sample_config():
    """Config with regular bindings and submap bindings."""
    config = Config(file_path="test.conf", original_content="")

    # Regular binding
    config.add_binding(Binding(
        type=BindType.BINDD,
        modifiers=["$mainMod"],
        key="Q",
        description="Close",
        action="killactive",
        params="",
        submap=None,
        line_number=0,
        category="Window Actions",
    ))

    # Submap entry binding
    config.add_binding(Binding(
        type=BindType.BIND,
        modifiers=["$mainMod"],
        key="R",
        description="Enter resize mode",
        action="submap",
        params="resize",
        submap=None,
        line_number=1,
        category="Modes",
    ))

    # Submap bindings
    config.add_binding(Binding(
        type=BindType.BIND,
        modifiers=[],
        key="h",
        description="Resize left",
        action="resizeactive",
        params="-10 0",
        submap="resize",
        line_number=2,
        category="Resize",
    ))

    config.add_binding(Binding(
        type=BindType.BIND,
        modifiers=[],
        key="l",
        description="Resize right",
        action="resizeactive",
        params="10 0",
        submap="resize",
        line_number=3,
        category="Resize",
    ))

    return config


def test_write_config_with_submaps(sample_config):
    """Write config with proper submap blocks."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.conf') as f:
        output_path = Path(f.name)

    try:
        ConfigWriter.write_file(sample_config, output_path)

        content = output_path.read_text()

        # Should have category sections
        assert "# ======= Window Actions =======" in content
        assert "# ======= Modes =======" in content

        # Should have submap block
        assert "# ======= Submaps =======" in content
        assert "submap = resize" in content
        assert "submap = reset" in content

        # Submap bindings should be between submap markers
        lines = content.split('\n')
        submap_start = None
        submap_end = None

        for i, line in enumerate(lines):
            if "submap = resize" in line:
                submap_start = i
            if submap_start is not None and "submap = reset" in line:
                submap_end = i
                break

        assert submap_start is not None
        assert submap_end is not None
        assert submap_end > submap_start

        # Check binding is in submap
        submap_content = "\n".join(lines[submap_start:submap_end+1])
        assert "resizeactive" in submap_content

    finally:
        output_path.unlink()
        backup = output_path.with_suffix(output_path.suffix + '.backup')
        if backup.exists():
            backup.unlink()


def test_write_creates_backup():
    """Backup is created before overwriting."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.conf') as f:
        output_path = Path(f.name)
        f.write("original content")

    try:
        config = Config(file_path=str(output_path), original_content="")
        ConfigWriter.write_file(config, output_path)

        backup_path = output_path.with_suffix(output_path.suffix + '.backup')
        assert backup_path.exists()

        backup_content = backup_path.read_text()
        assert "original content" in backup_content

    finally:
        output_path.unlink()
        backup = output_path.with_suffix(output_path.suffix + '.backup')
        if backup.exists():
            backup.unlink()


def test_atomic_write_on_failure():
    """Failed write cleans up temp files on error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.conf"
        output_path.write_text("original content")

        # Create invalid config that will fail during content generation
        # We'll monkey-patch generate_content to raise an error
        config = Config(file_path=str(output_path), original_content="")

        original_generate = ConfigWriter.generate_content

        def failing_generate(cfg):
            raise ValueError("Test error during generation")

        ConfigWriter.generate_content = failing_generate

        try:
            with pytest.raises(IOError) as exc_info:
                ConfigWriter.write_file(config, output_path)

            # Should mention the error
            assert "Failed to write config" in str(exc_info.value)

            # No temp files should remain
            temp_files = list(Path(tmpdir).glob(".hyprbind_tmp_*"))
            assert len(temp_files) == 0, f"Temp files not cleaned up: {temp_files}"

            # Original file should still exist with original content
            assert output_path.exists()
            content = output_path.read_text()
            assert "original content" in content

        finally:
            # Restore original method
            ConfigWriter.generate_content = original_generate
