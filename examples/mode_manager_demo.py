#!/usr/bin/env python3
"""
Mode Manager Demo
Demonstrates the Safe/Live mode toggle functionality.

This script shows how to use ModeManager to switch between:
- Safe mode: File-only changes (requires Hyprland reload)
- Live mode: IPC changes (immediate testing, temporary)
"""

from pathlib import Path
from hyprbind.core.config_manager import ConfigManager
from hyprbind.core.mode_manager import ModeManager, Mode
from hyprbind.core.models import Binding, BindType


def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def main():
    """Run mode manager demonstration."""
    print_section("HyprBind Mode Manager Demo")

    # Create a sample binding
    sample_binding = Binding(
        type=BindType.BINDD,
        modifiers=["$mainMod"],
        key="T",
        description="Open terminal",
        action="exec",
        params="alacritty",
        submap=None,
        line_number=1,
        category="Applications",
    )

    print(f"Sample binding: {sample_binding.display_name}")
    print(f"Description: {sample_binding.description}")
    print(f"Action: {sample_binding.action} {sample_binding.params}")

    # Initialize ConfigManager (using test config path)
    test_config_path = Path("/tmp/hyprbind_test_keybinds.conf")
    config_manager = ConfigManager(test_config_path)

    # Initialize ModeManager
    mode_manager = ModeManager(config_manager)

    print_section("Mode Manager Status")
    print(f"Current mode: {mode_manager.get_mode().value}")
    print(f"Live mode available: {mode_manager.is_live_available()}")

    # Demonstrate Safe mode
    print_section("Safe Mode (Default)")
    print("In Safe mode, bindings are written to config file only.")
    print("Hyprland must be reloaded for changes to take effect.\n")

    result = mode_manager.apply_binding(sample_binding, "add")
    print(f"Add binding result: {result.success}")
    print(f"Message: {result.message}")

    # Try to switch to Live mode
    print_section("Attempting to Switch to Live Mode")

    if mode_manager.is_live_available():
        print("Hyprland is running - Live mode available!")

        # Confirm with user
        print("\nLive mode will:")
        print("  • Send changes directly to Hyprland via IPC")
        print("  • Apply changes immediately (no reload needed)")
        print("  • Keep changes temporary (until saved to file)")
        print("  • Revert changes when HyprBind closes")

        response = input("\nEnable Live mode? (y/n): ")
        if response.lower() == "y":
            if mode_manager.set_mode(Mode.LIVE):
                print("\n✓ Live mode enabled!")
                print(f"Current mode: {mode_manager.get_mode().value}")

                # Demonstrate Live mode
                print_section("Live Mode Operations")

                print("Adding binding via IPC...")
                result = mode_manager.apply_binding(sample_binding, "add")
                print(f"Result: {result.success}")
                print(f"Message: {result.message}")

                print("\nRemoving binding via IPC...")
                result = mode_manager.apply_binding(sample_binding, "remove")
                print(f"Result: {result.success}")
                print(f"Message: {result.message}")
            else:
                print("\n✗ Failed to enable Live mode")
        else:
            print("\nStaying in Safe mode")
    else:
        print("Hyprland is not running - Live mode unavailable")
        print("\nTo use Live mode:")
        print("  1. Make sure Hyprland is running")
        print("  2. Ensure HYPRLAND_INSTANCE_SIGNATURE is set")
        print("  3. Verify IPC socket exists")

    # Switch back to Safe mode
    if mode_manager.get_mode() == Mode.LIVE:
        print_section("Switching Back to Safe Mode")
        mode_manager.set_mode(Mode.SAFE)
        print(f"Current mode: {mode_manager.get_mode().value}")

    print_section("Demo Complete")
    print("Key takeaways:")
    print("  • Safe mode: Changes written to file only")
    print("  • Live mode: Changes via IPC, immediate testing")
    print("  • Use Live mode to test bindings before committing")
    print("  • Always save to file if you want to keep changes")
    print()


if __name__ == "__main__":
    main()
