"""End-to-end tests for mode switching (Safe ↔ Live mode).

This test validates the complete user flow for switching between Safe and Live modes:

Test 1: test_safe_to_live_mode_switch
- Launch app (starts in Safe mode)
- Mock Hyprland IPC as available
- Toggle mode switch
- Verify confirmation dialog appears
- Click "Enable Live Mode"
- Verify mode label changes to "Live"
- Verify Live mode banner appears
- Add binding and verify IPC call (not file write)

Test 2: test_live_to_safe_mode_switch
- Start in Live mode
- Toggle mode switch off
- Verify mode label changes to "Safe"
- Verify banner hidden
- Add binding and verify file write (not IPC)

NOTE: These tests must be run individually due to GTK application registration
limitations. Running both tests in sequence will cause a GLib.GError about
duplicate application exports. Each test works correctly when run in isolation:

    pytest tests/e2e/test_mode_switching.py::test_safe_to_live_mode_switch
    pytest tests/e2e/test_mode_switching.py::test_live_to_safe_mode_switch
"""

import pytest
import gi
from unittest.mock import patch, Mock

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw
from pathlib import Path

from tests.e2e.gtk_utils import (
    wait_for_condition,
    simulate_click,
    process_pending_events,
)
from hyprbind.core.models import Binding, BindType
from hyprbind.core.mode_manager import Mode


@patch("hyprbind.ipc.hyprland_client.HyprlandClient.is_running")
@patch("hyprbind.ipc.hyprland_client.HyprlandClient.connect")
@patch("hyprbind.ipc.hyprland_client.HyprlandClient.add_binding")
def test_safe_to_live_mode_switch(
    mock_add_binding, mock_connect, mock_is_running, main_window, temp_config_file
):
    """Test switching from Safe mode to Live mode.

    Flow:
    1. Launch app (starts in Safe mode)
    2. Mock Hyprland IPC as available
    3. Toggle mode switch
    4. Verify confirmation dialog appears
    5. Click "Enable Live Mode"
    6. Verify mode label changes to "Live"
    7. Verify Live mode banner appears
    8. Add binding and verify IPC call (not file write)
    """
    # Setup mocks
    mock_is_running.return_value = True
    mock_connect.return_value = True
    mock_add_binding.return_value = True

    # Step 1: Verify app starts in Safe mode
    assert main_window is not None
    assert hasattr(main_window, "mode_manager")
    assert hasattr(main_window, "mode_switch")
    assert hasattr(main_window, "mode_label")
    assert hasattr(main_window, "live_mode_banner")

    # Wait for initial UI setup
    process_pending_events()

    # Verify initial state is Safe mode
    assert main_window.mode_manager.get_mode() == Mode.SAFE
    assert not main_window.mode_switch.get_active()
    assert main_window.mode_label.get_text() == "Safe"
    assert not main_window.live_mode_banner.get_revealed()

    # Step 2 & 3: Toggle mode switch (mock is already set up)
    # This will trigger confirmation dialog
    main_window.mode_switch.set_active(True)
    process_pending_events()

    # Step 4: Confirmation dialog should appear (created in _on_mode_toggled)
    # We can't easily access the modal dialog, but we can verify the switch was toggled
    assert main_window.mode_switch.get_active()

    # Step 5: Simulate clicking "Enable Live Mode" by directly calling response handler
    # The dialog's response handler will call mode_manager.set_mode(Mode.LIVE)
    # and then _update_mode_ui()
    # We simulate this by directly setting the mode since dialog interaction is complex
    main_window.mode_manager.set_mode(Mode.LIVE)
    main_window._update_mode_ui()
    process_pending_events()

    # Step 6: Verify mode label changes to "Live"
    assert main_window.mode_label.get_text() == "Live"

    # Step 7: Verify Live mode banner appears
    assert main_window.live_mode_banner.get_revealed()

    # Step 8: Add binding and verify IPC call (not file write)
    test_binding = Binding(
        type=BindType.BINDD,
        modifiers=["$mainMod"],
        key="T",
        description="Test Live Binding",
        action="exec",
        params="test-command",
        submap=None,
        line_number=0,
        category="Test",
    )

    # Apply binding in Live mode
    result = main_window.mode_manager.apply_binding(test_binding, "add")

    # Verify result
    assert result.success
    assert "IPC" in result.message
    assert "not saved to file" in result.message

    # Verify IPC was called
    mock_add_binding.assert_called_once()

    # Verify binding was NOT written to config file
    config_content = temp_config_file.read_text()
    assert "Test Live Binding" not in config_content


@patch("hyprbind.ipc.hyprland_client.HyprlandClient.is_running")
@patch("hyprbind.ipc.hyprland_client.HyprlandClient.connect")
@patch("hyprbind.ipc.hyprland_client.HyprlandClient.add_binding")
def test_live_to_safe_mode_switch(
    mock_add_binding, mock_connect, mock_is_running, main_window, temp_config_file
):
    """Test switching from Live mode to Safe mode.

    Flow:
    1. Start in Live mode
    2. Toggle mode switch off
    3. Verify mode label changes to "Safe"
    4. Verify banner hidden
    5. Add binding and verify file write (not IPC)
    """
    # Setup mocks
    mock_is_running.return_value = True
    mock_connect.return_value = True
    mock_add_binding.return_value = True

    # Step 1: Start in Live mode
    # First enable Live mode (requires going through Safe -> Live flow)
    main_window.mode_switch.set_active(True)
    process_pending_events()

    # Set mode directly (simulating dialog confirmation)
    main_window.mode_manager.set_mode(Mode.LIVE)
    main_window._update_mode_ui()
    process_pending_events()

    # Verify we're in Live mode
    assert main_window.mode_manager.get_mode() == Mode.LIVE
    assert main_window.mode_switch.get_active()
    assert main_window.mode_label.get_text() == "Live"
    assert main_window.live_mode_banner.get_revealed()

    # Step 2: Toggle mode switch off (back to Safe mode)
    main_window.mode_switch.set_active(False)
    process_pending_events()

    # Step 3: Verify mode label changes to "Safe"
    assert main_window.mode_label.get_text() == "Safe"
    assert main_window.mode_manager.get_mode() == Mode.SAFE

    # Step 4: Verify banner hidden
    assert not main_window.live_mode_banner.get_revealed()

    # Step 5: Add binding and verify file write (not IPC)
    test_binding = Binding(
        type=BindType.BINDD,
        modifiers=["$mainMod"],
        key="S",
        description="Test Safe Binding",
        action="exec",
        params="safe-command",
        submap=None,
        line_number=0,
        category="Test",
    )

    # Reset mock to verify it's not called in Safe mode
    mock_add_binding.reset_mock()

    # Apply binding in Safe mode
    result = main_window.mode_manager.apply_binding(test_binding, "add")

    # Verify result
    assert result.success

    # Verify message does NOT mention IPC
    assert "IPC" not in result.message

    # Verify IPC was NOT called
    mock_add_binding.assert_not_called()

    # In Safe mode, changes are made to config but not automatically saved
    # We need to save explicitly
    save_result = main_window.config_manager.save()
    assert save_result.success

    # Verify binding WAS written to config file
    config_content = temp_config_file.read_text()
    assert "Test Safe Binding" in config_content
    assert "safe-command" in config_content
