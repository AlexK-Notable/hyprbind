# End-to-End Testing Design

**Date:** 2025-01-13
**Status:** Approved
**Approach:** Headless GTK testing with GLib.MainContext

## Overview

Implement comprehensive end-to-end tests that validate complete user workflows from UI interaction through to file/IPC operations. Tests run headless for speed and CI/CD compatibility, covering critical user journeys.

## Goals

1. **Validate Complete Workflows** - Test full user interactions from launch to file modification
2. **Fast & Reliable** - Headless execution suitable for CI/CD pipelines
3. **Maintainable** - Clear test structure with reusable utilities
4. **Focused Scope** - Cover core user journeys (YAGNI approach)

## Architecture

### Directory Structure

```
tests/e2e/
├── conftest.py              # E2E fixtures and setup
├── app_lifecycle.py         # Application launch/shutdown
├── gtk_utils.py             # Event loop and widget utilities
├── test_add_binding.py      # Add binding workflow
├── test_edit_binding.py     # Edit binding workflow
├── test_delete_binding.py   # Delete binding workflow
├── test_mode_switching.py   # Safe/Live mode toggle
└── test_config_lifecycle.py # Load/save configuration
```

### Core Components

#### 1. Application Lifecycle Manager (`app_lifecycle.py`)

Handles the complete lifecycle of launching and shutting down the GTK application in headless mode.

**Key Functions:**
- `setup_headless_display()` - Configure GTK for headless operation
- `launch_app(config_path)` - Start application without blocking main loop
- `shutdown_app(app)` - Graceful cleanup of GTK resources
- `ApplicationContext` - Context manager for app lifecycle

**Headless Strategy:**
```python
# Set GDK backend to broadway (headless HTML5 backend)
os.environ['GDK_BACKEND'] = 'broadway'
# Or use Xvfb virtual display if broadway unavailable
```

#### 2. Event Loop Utilities (`gtk_utils.py`)

Provides utilities for managing GTK event loop in tests, allowing synchronous test code to work with async GTK operations.

**Key Functions:**
- `wait_for_condition(predicate, timeout=5.0)` - Poll condition while processing events
- `process_pending_events(max_iterations=100)` - Drain GTK event queue
- `wait_for_window_visible(window, timeout=5.0)` - Wait for window to appear
- `find_widget_by_name(container, name)` - Locate widgets in hierarchy
- `simulate_click(widget)` - Programmatically activate widgets
- `simulate_text_entry(entry, text)` - Type text into entry fields

**Example Usage:**
```python
# Click button and wait for dialog
simulate_click(add_button)
wait_for_condition(lambda: dialog.is_visible(), timeout=2.0)

# Fill form and wait for validation
simulate_text_entry(key_entry, "Q")
process_pending_events()
assert not error_label.is_visible()
```

#### 3. E2E Fixtures (`conftest.py`)

Pytest fixtures providing test isolation and setup.

**Fixtures:**
- `headless_display` (session) - One-time headless display setup
- `temp_config_file` (function) - Temporary Hyprland config for each test
- `e2e_app` (function) - Fresh application instance per test
- `main_window` (function) - Launched main window with test config
- `mock_hyprland_socket` (function) - Mock IPC socket for Live mode tests

**Cleanup Strategy:**
- Ensure `shutdown_app()` called even on test failure
- Remove temporary config files
- Close all windows and dialogs
- Clear GTK event queue

## Test Scenarios

### 1. Add Binding Workflow (`test_add_binding.py`)

**Test:** `test_add_binding_end_to_end`

**Steps:**
1. Launch app with empty config
2. Click "Add" button in Editor tab
3. Fill binding form (key, modifiers, description, action)
4. Click "Save"
5. Verify dialog closes
6. Verify binding appears in editor list
7. Verify binding written to config file

**Assertions:**
- Binding visible in UI list
- Config file contains new binding line
- Binding has correct format (bindd syntax)

### 2. Edit Binding Workflow (`test_edit_binding.py`)

**Test:** `test_edit_binding_end_to_end`

**Steps:**
1. Launch app with pre-populated config
2. Select existing binding in list
3. Click "Edit" button
4. Modify key from Q to W
5. Click "Save"
6. Verify dialog closes
7. Verify updated binding in list
8. Verify config file updated

**Assertions:**
- Old binding removed from file
- New binding added with correct line number
- UI reflects changes immediately

### 3. Delete Binding Workflow (`test_delete_binding.py`)

**Test:** `test_delete_binding_with_confirmation`

**Steps:**
1. Launch app with test config
2. Select binding to delete
3. Click "Delete" button
4. Verify confirmation dialog appears
5. Click "Delete" in dialog
6. Verify binding removed from list
7. Verify binding removed from config file

**Assertions:**
- Confirmation dialog shows correct binding description
- Binding removed from UI immediately after confirmation
- Config file no longer contains binding

### 4. Mode Switching (`test_mode_switching.py`)

**Test:** `test_safe_to_live_mode_switch`

**Steps:**
1. Launch app (starts in Safe mode)
2. Mock Hyprland IPC as available
3. Toggle mode switch
4. Verify confirmation dialog appears
5. Click "Enable Live Mode"
6. Verify mode label changes to "Live"
7. Verify Live mode banner appears
8. Add binding and verify IPC call (not file write)

**Assertions:**
- Mode label shows "Live"
- Banner revealed
- Binding operations use IPC client
- Config file not modified until "Save Now"

**Test:** `test_live_to_safe_mode_switch`

**Steps:**
1. Start in Live mode
2. Toggle mode switch off
3. Verify mode label changes to "Safe"
4. Verify banner hidden
5. Add binding and verify file write (not IPC)

### 5. Config Lifecycle (`test_config_lifecycle.py`)

**Test:** `test_load_and_save_config`

**Steps:**
1. Create test config file with 5 bindings
2. Launch app
3. Wait for config to load (async operation)
4. Verify 5 bindings appear in editor
5. Modify one binding
6. Trigger save (via menu or Ctrl+S)
7. Reload config from file
8. Verify modification persisted

**Assertions:**
- All bindings loaded correctly
- Categories parsed properly
- File writes are atomic
- No data loss on save/reload

## Error Handling & Edge Cases

### Timeout Handling
- All `wait_for_condition` calls have explicit timeouts (default 5s)
- Timeouts raise clear exceptions with context
- Tests fail fast on timeout rather than hanging

### Resource Cleanup
- Use pytest fixtures with yield for guaranteed cleanup
- Context managers for app lifecycle
- Teardown runs even on assertion failures

### GTK Warnings
- Suppress expected GTK warnings in headless mode
- Log unexpected warnings for investigation
- Don't fail tests on cosmetic GTK messages

## Testing Strategy

### Headless Display Setup

**Option 1: Broadway Backend (Preferred)**
```python
os.environ['GDK_BACKEND'] = 'broadway'
os.environ['BROADWAY_DISPLAY'] = ':5'
```

**Option 2: Xvfb (Fallback)**
```python
# Start Xvfb in fixture
display = Xvfb(width=1024, height=768)
display.start()
yield
display.stop()
```

### Event Loop Management

**Pattern:**
```python
def wait_for_condition(predicate, timeout=5.0):
    """Wait for condition while processing GTK events."""
    start = time.time()
    context = GLib.MainContext.default()

    while time.time() - start < timeout:
        if predicate():
            return True
        # Process pending events
        while context.pending():
            context.iteration(False)
        time.sleep(0.01)

    raise TimeoutError(f"Condition not met within {timeout}s")
```

### Widget Interaction

**Finding Widgets:**
```python
def find_widget_by_name(container, name):
    """Recursively find widget by name."""
    if container.get_name() == name:
        return container

    child = container.get_first_child()
    while child:
        result = find_widget_by_name(child, name)
        if result:
            return result
        child = child.get_next_sibling()

    return None
```

**Simulating Clicks:**
```python
def simulate_click(widget):
    """Programmatically activate widget."""
    if isinstance(widget, Gtk.Button):
        widget.emit("clicked")
    elif isinstance(widget, Gtk.Switch):
        widget.set_active(not widget.get_active())
    # Process resulting events
    process_pending_events()
```

## Dependencies

**Required Packages:**
- `pytest` - Test framework (already installed)
- `pytest-timeout` - Timeout management (new)
- `python-xvfb` - Virtual display (optional, fallback)

**GTK Configuration:**
- Broadway backend support (included in GTK4)
- No additional system packages required

## Success Criteria

1. ✅ All 5-7 E2E test scenarios pass
2. ✅ Tests run headless without display
3. ✅ Tests complete in < 30 seconds total
4. ✅ No resource leaks (windows, files, processes)
5. ✅ Clear failure messages on test failures
6. ✅ Works in CI/CD environment

## Future Enhancements

**Not in Initial Scope (YAGNI):**
- Visual regression testing (screenshots)
- Extended workflows (export, import, backup)
- Performance benchmarking
- Stress testing (large configs)
- Accessibility testing

These can be added later if needed, but core user journeys take priority.

## Implementation Notes

### Test Isolation
- Each test gets fresh app instance
- Temporary config files per test
- No shared state between tests
- Clean GTK event queue between tests

### Debugging
- Set `DEBUG=1` environment variable for verbose GTK output
- `pytest -s` to see print statements
- `pytest -vv` for detailed assertion output
- Add `time.sleep()` to pause and inspect state

### CI/CD Integration
```yaml
# GitHub Actions example
- name: Run E2E Tests
  run: |
    export GDK_BACKEND=broadway
    pytest tests/e2e/ -v --timeout=60
```

## Conclusion

This design provides a focused, maintainable E2E test suite that validates critical user workflows. The headless approach ensures fast, reliable execution suitable for CI/CD pipelines. By focusing on core journeys and using YAGNI principles, we avoid over-testing while still catching integration issues.
