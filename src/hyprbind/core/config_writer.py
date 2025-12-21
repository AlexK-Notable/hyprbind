"""Config file writer with atomic writes and submap support."""

from pathlib import Path
from typing import List, Dict
import tempfile
import shutil
import os

from hyprbind.core.models import Config, Binding
from hyprbind.core.logging_config import get_logger
from hyprbind.core.validators import PathValidator

logger = get_logger(__name__)


class ConfigWriter:
    """Writes Config objects to Hyprland config files."""

    @staticmethod
    def write_file(config: Config, output_path: Path, skip_validation: bool = False) -> None:
        """Write config to file atomically with backup.

        Args:
            config: Config object to write
            output_path: Path to output file
            skip_validation: Skip path validation (for testing with tmp paths)

        Raises:
            ValueError: If path fails security validation
            IOError: If write fails
        """
        # Validate path before writing
        if not skip_validation:
            path_error = PathValidator.validate_write_path(output_path)
            if path_error:
                logger.warning("Write path validation failed: %s (%s)", output_path, path_error)
                raise ValueError(path_error)

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
            except OSError as cleanup_error:
                # Temp file cleanup is non-critical; log for debugging
                logger.debug("Failed to cleanup temp file %s: %s", temp_path, cleanup_error)
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
            bindings = [b for b in config.categories[category].bindings if not b.submap]

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
