"""End-to-end test for the config lifecycle (load → modify → save → reload).

This test validates the complete configuration lifecycle workflow:
1. Create test config file with 5 bindings
2. Launch app
3. Wait for config to load (async operation)
4. Verify 5 bindings appear in editor
5. Modify one binding
6. Trigger save (via config_manager.save())
7. Reload config from file
8. Verify modification persisted

This ensures the full data flow works correctly from file → memory → UI → file.
"""

import pytest
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw
from pathlib import Path

from tests.e2e.gtk_utils import (
    wait_for_condition,
    find_widget_by_name,
    simulate_click,
    simulate_text_entry,
    process_pending_events,
)


def test_load_and_save_config(main_window, temp_config_file):
    """Test complete config lifecycle: load → modify → save → reload.

    This test validates the entire configuration lifecycle:
    - Initial config loading (async operation in background thread)
    - Bindings appear correctly in UI
    - Modifying a binding in memory
    - Saving config to file (atomic write with backup)
    - Reloading config from file
    - Verifying modifications persisted correctly
    - File format integrity maintained

    Args:
        main_window: MainWindow fixture (from conftest.py)
        temp_config_file: Path to temporary config file with 5 sample bindings (from conftest.py)
    """
    # Step 1: Verify app launched with editor tab
    assert main_window is not None
    assert hasattr(main_window, "editor_tab")
    editor_tab = main_window.editor_tab

    # Get config_manager for direct access to save/load operations
    assert hasattr(main_window, "config_manager")
    config_manager = main_window.config_manager

    # Step 2: Wait for async config load to complete
    # Config loading happens in background thread (main_window.py line 234-247)
    def config_loaded():
        """Check if config has been loaded."""
        return editor_tab.list_store.get_n_items() > 0

    wait_for_condition(config_loaded, timeout=3.0)

    # Step 3: Verify bindings appear in editor
    # list_store contains both category headers AND bindings
    # temp_config has 2 category headers + 5 bindings = 7 items total
    initial_count = editor_tab.list_store.get_n_items()
    assert initial_count == 7, f"Expected 7 items (2 headers + 5 bindings) from temp config, got {initial_count}"

    # Count initial bindings for later verification
    initial_binding_count = 0
    for i in range(initial_count):
        item = editor_tab.list_store.get_item(i)
        if not item.is_header and item.binding:
            initial_binding_count += 1

    assert initial_binding_count == 5, f"Expected 5 bindings in temp config, got {initial_binding_count}"

    # Step 4: Select first binding to modify
    selected_position = None
    target_binding = None

    for i in range(editor_tab.list_store.get_n_items()):
        item = editor_tab.list_store.get_item(i)
        if not item.is_header and item.binding:
            binding = item.binding
            selected_position = i
            target_binding = binding
            break

    assert target_binding is not None, "Should find at least one binding in the list"
    assert selected_position is not None, "Should find position of a binding"

    # Store original values for verification
    original_key = target_binding.key
    original_description = target_binding.description
    original_action = target_binding.action
    original_modifiers = target_binding.modifiers
    original_params = target_binding.params

    # Step 5: Modify the binding (change key to "MODIFIED_KEY")
    # Create new binding with modified key
    from hyprbind.core.models import Binding

    new_key = "MODIFIED_KEY"
    modified_binding = Binding(
        type=target_binding.type,
        modifiers=original_modifiers,
        key=new_key,
        description=original_description,
        action=original_action,
        params=original_params,
        submap=target_binding.submap,
        line_number=target_binding.line_number,
        category=target_binding.category,
    )

    # Update the binding in config_manager
    result = config_manager.update_binding(target_binding, modified_binding)
    assert result.success, f"Failed to update binding: {result.message}"

    # Verify dirty flag is set
    assert config_manager.is_dirty(), "Config should be marked as dirty after modification"

    # Step 6: Save config to file
    # Save to the temp config file (the test fixture path)
    save_result = config_manager.save(temp_config_file)
    assert save_result.success, f"Failed to save config: {save_result.message}"

    # Verify dirty flag is cleared after save
    assert not config_manager.is_dirty(), "Config should not be dirty after save"

    # Step 7: Reload config from file (on GTK main thread)
    # This simulates app restart or manual reload
    # CRITICAL: Must run on main thread to avoid GTK threading violations
    import threading
    from gi.repository import GLib

    reload_complete = threading.Event()
    reloaded_config = None
    reload_error = None

    def reload_on_main_thread():
        nonlocal reloaded_config, reload_error
        try:
            reloaded_config = config_manager.load()
        except Exception as e:
            reload_error = e
        reload_complete.set()
        return False  # Don't repeat idle call

    GLib.idle_add(reload_on_main_thread)

    # Wait for reload to complete, processing GTK events while waiting
    import time
    start_time = time.time()
    timeout = 5.0
    context = GLib.MainContext.default()

    while not reload_complete.is_set() and (time.time() - start_time < timeout):
        # Process pending GTK events to allow idle_add callback to execute
        while context.pending():
            context.iteration(False)
        time.sleep(0.01)  # Small sleep to avoid busy-waiting

    assert reload_complete.is_set(), "Config reload timed out"
    assert reload_error is None, f"Config reload failed: {reload_error}"
    assert reloaded_config is not None, "Config should reload successfully"

    # Wait for UI to update after reload (observer pattern notification)
    def ui_updated():
        """Check if UI has been updated with reloaded config."""
        # The list_store should still have items after reload
        return editor_tab.list_store.get_n_items() > 0

    wait_for_condition(ui_updated, timeout=2.0)

    # Step 8: Verify modification persisted in memory
    # Find the modified binding in the reloaded config
    found_modified_binding = False
    found_old_binding = False

    # Check all bindings in all categories
    for category in reloaded_config.categories.values():
        for binding in category.bindings:
            # Check for modified binding (new key with same description)
            if (binding.key == new_key and
                binding.description == original_description and
                binding.action == original_action):
                found_modified_binding = True
            # Check for old binding (original key with same description) - should NOT exist
            if (binding.key == original_key and
                binding.description == original_description and
                binding.action == original_action):
                found_old_binding = True

    assert found_modified_binding, f"Modified binding ({new_key} key) should exist after reload"
    assert not found_old_binding, f"Old binding ({original_key} key) should not exist after reload"

    # Step 9: Verify modification persisted in file
    config_content = temp_config_file.read_text()

    # The new binding should be in the config file
    assert new_key in config_content, (
        f"Config file should contain modified binding with {new_key} key.\n"
        f"Config content:\n{config_content}"
    )

    # Verify the binding appears with correct format
    # Check that description and action are also present on same line or nearby
    config_lines = config_content.split('\n')
    found_complete_binding = False
    for line in config_lines:
        # Check if this line contains the modified binding
        # bindd format: bindd = modifiers, key, description, action[, params]
        if new_key in line and original_description in line:
            found_complete_binding = True
            break

    assert found_complete_binding, (
        f"Config file should contain complete modified binding.\n"
        f"Expected to find line with: {new_key} and {original_description}\n"
        f"Config content:\n{config_content}"
    )

    # Step 10: Verify old binding is removed from file
    # The old key should not appear with the same description and action
    # (We check for the combination because the key alone might appear elsewhere)
    old_binding_exists = False
    for line in config_lines:
        # Check if line contains the old key along with the same description
        # This ensures we're looking at the exact binding we modified, not just any binding with that key
        if (original_key in line and
            original_description in line and
            new_key not in line):  # Make sure it's not the modified version
            old_binding_exists = True
            break

    assert not old_binding_exists, (
        f"Old binding should be removed from config.\n"
        f"Expected NOT to find line with key '{original_key}' and description '{original_description}' (without '{new_key}')\n"
        f"Config content:\n{config_content}"
    )

    # Step 11: Verify file format integrity
    # Config file should still be valid with proper structure
    # Check for category headers (lines starting with #)
    has_category_headers = any(line.strip().startswith('#') for line in config_lines)
    assert has_category_headers, "Config file should maintain category headers"

    # Check that we have binding lines in the file
    # (Note: File may have more lines than parsed bindings due to comments, submaps, etc.)
    binding_lines = [line for line in config_lines if line.strip().startswith(('bindd', 'bind ', 'bindm', 'bindel'))]
    assert len(binding_lines) > 0, "Config file should contain binding lines"
    assert len(binding_lines) == initial_binding_count, (
        f"Config file should have exactly {initial_binding_count} binding lines, found {len(binding_lines)}"
    )

    # Step 12: Verify bindings exist after reload (no total loss)
    # Count bindings in reloaded config
    total_bindings = sum(len(cat.bindings) for cat in reloaded_config.categories.values())
    assert total_bindings > 0, "Should have bindings after reload (no total data loss)"

    # Verify categories are preserved
    assert len(reloaded_config.categories) > 0, "Should have at least one category after reload"

    # Step 13: Verify atomic write (no corruption)
    # If file exists and has content, it should be parseable
    assert temp_config_file.exists(), "Config file should exist after save"
    assert temp_config_file.stat().st_size > 0, "Config file should not be empty"

    # Try parsing the file again to ensure it's valid
    from hyprbind.parsers.config_parser import ConfigParser
    parsed_config = ConfigParser.parse_file(temp_config_file)
    assert parsed_config is not None, "Saved config file should be parseable"

    # Verify parsed config has bindings
    parsed_binding_count = sum(len(cat.bindings) for cat in parsed_config.categories.values())
    assert parsed_binding_count > 0, "Parsed config should have bindings (no data loss)"
