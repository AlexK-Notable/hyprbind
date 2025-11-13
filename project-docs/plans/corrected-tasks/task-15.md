# Task 15: Config File Writer (CORRECTED)
**Corrections Applied**: Submap handling, atomic writes with backup

---

## ConfigWriter (Complete Corrected Implementation)

**File**: `src/hyprbind/core/config_writer.py`

```python
"""Config file writer with atomic writes and submap support."""

from pathlib import Path
from typing import List, Dict
import tempfile
import shutil
import os

from hyprbind.core.models import Config, Binding


class ConfigWriter:
    """Writes Config objects to Hyprland config files."""

    @staticmethod
    def write_file(config: Config, output_path: Path) -> None:
        """Write config to file atomically with backup.

        Args:
            config: Config object to write
            output_path: Path to output file

        Raises:
            IOError: If write fails
        """
        # Create backup if file exists
        if output_path.exists():
            backup_path = output_path.with_suffix(output_path.suffix + '.backup')
            shutil.copy2(output_path, backup_path)

        # Write to temporary file first
        temp_fd, temp_path = tempfile.mkstemp(
            dir=output_path.parent,
            prefix='.hyprbind_tmp_',
            suffix='.conf'
        )

        try:
            with os.fdopen(temp_fd, 'w') as f:
                lines = ConfigWriter.generate_content(config)
                content = "\n".join(lines)
                f.write(content)
                f.flush()
                os.fsync(f.fileno())  # Force to disk

            # Atomic replace (POSIX rename is atomic)
            os.replace(temp_path, output_path)

        except Exception as e:
            # Clean up temp file on error
            try:
                os.unlink(temp_path)
            except:
                pass
            raise IOError(f"Failed to write config: {e}")

    @staticmethod
    def generate_content(config: Config) -> List[str]:
        """Generate config file content with proper submap handling.

        Args:
            config: Config object

        Returns:
            List of lines for config file
        """
        lines = []

        # First: Non-submap bindings grouped by category
        for category in sorted(config.categories.keys()):
            bindings = [b for b in config.categories[category] if not b.submap]

            if not bindings:
                continue

            # Category header
            lines.append("")
            lines.append(f"# ======= {category} =======")

            # Bindings
            for binding in bindings:
                lines.append(ConfigWriter._format_binding(binding))

        # Second: Submap bindings grouped by submap name
        submaps: Dict[str, List[Binding]] = {}
        for binding in config.get_all_bindings():
            if binding.submap:
                if binding.submap not in submaps:
                    submaps[binding.submap] = []
                submaps[binding.submap].append(binding)

        if submaps:
            lines.append("")
            lines.append("# ======= Submaps =======")

            for submap_name in sorted(submaps.keys()):
                bindings = submaps[submap_name]

                lines.append("")
                lines.append(f"submap = {submap_name}")

                for binding in bindings:
                    lines.append(ConfigWriter._format_binding(binding))

                lines.append("submap = reset")

        return lines

    @staticmethod
    def _format_binding(binding: Binding) -> str:
        """Format a binding as a config line.

        Args:
            binding: Binding to format

        Returns:
            Formatted config line
        """
        bind_type = binding.type.value

        # Modifiers
        mods = ", ".join(binding.modifiers) if binding.modifiers else ""

        # Build line based on type
        if binding.type.value == "bindd":
            # bindd = MODS, KEY, Description, action, params
            return f"{bind_type} = {mods}, {binding.key}, {binding.description}, {binding.action}, {binding.params or ''}"
        elif binding.type.value == "bind":
            # bind = MODS, KEY, action, params
            return f"{bind_type} = {mods}, {binding.key}, {binding.action}, {binding.params or ''}"
        elif binding.type.value == "bindel":
            # bindel = MODS, KEY, action, params
            return f"{bind_type} = {mods}, {binding.key}, {binding.action}, {binding.params or ''}"
        elif binding.type.value == "bindm":
            # bindm = MODS, KEY, action, params
            return f"{bind_type} = {mods}, {binding.key}, {binding.action}, {binding.params or ''}"
        else:
            # Generic fallback
            return f"{bind_type} = {mods}, {binding.key}, {binding.action}, {binding.params or ''}"
```

**Tests** (`tests/core/test_config_writer.py`):

```python
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
    """Failed write doesn't corrupt original file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.conf') as f:
        output_path = Path(f.name)
        f.write("original content")

    try:
        # Create config with invalid data that will fail during write
        config = Config(file_path=str(output_path), original_content="")

        # Make directory read-only to force write failure
        output_path.parent.chmod(0o444)

        with pytest.raises(IOError):
            ConfigWriter.write_file(config, output_path)

        # Original file should still exist with original content
        assert output_path.exists()
        content = output_path.read_text()
        assert "original content" in content

    finally:
        # Restore permissions
        output_path.parent.chmod(0o755)
        output_path.unlink()
```

**ConfigManager Integration** (add to `src/hyprbind/core/config_manager.py`):

```python
from hyprbind.core.config_writer import ConfigWriter

def save(self, output_path: Optional[Path] = None) -> OperationResult:
    """Save config to file.

    Args:
        output_path: Path to save to (defaults to config_path)

    Returns:
        OperationResult with success status
    """
    if not self.config:
        return OperationResult(
            success=False,
            message="Config not loaded - nothing to save",
        )

    target_path = output_path or self.config_path

    try:
        ConfigWriter.write_file(self.config, target_path)
        self._dirty = False
        return OperationResult(
            success=True,
            message=f"Config saved to {target_path}",
        )
    except Exception as e:
        return OperationResult(
            success=False,
            message=f"Failed to save config: {e}",
        )
```

---

Key: Atomic writes, backup creation, proper submap block handling, comprehensive error handling.
