# Mode Manager UI Integration Guide

This document describes how to integrate the Mode Manager (Safe/Live toggle) into the MainWindow UI.

## Overview

The Mode Manager provides two operating modes:

- **Safe Mode** (default): Changes are written to config file only. Requires Hyprland reload to take effect. Safe for experimentation.
- **Live Mode**: Changes are sent via IPC to running Hyprland for immediate testing. Changes are temporary unless explicitly saved.

## Implementation Steps

### 1. Update UI Template (`data/ui/main_window.ui`)

Add mode toggle controls to the header bar:

```xml
<!-- Add to header bar section -->
<child type="end">
  <object class="GtkBox" id="mode_controls_box">
    <property name="spacing">12</property>
    <property name="margin-end">12</property>

    <!-- Mode indicator label -->
    <child>
      <object class="GtkLabel" id="mode_label">
        <property name="label">Mode:</property>
        <style>
          <class name="dim-label"/>
        </style>
      </object>
    </child>

    <!-- Mode toggle switch -->
    <child>
      <object class="GtkSwitch" id="mode_switch">
        <property name="valign">center</property>
        <property name="tooltip-text">Toggle between Safe mode (file-only) and Live mode (IPC testing)</property>
      </object>
    </child>

    <!-- Current mode display -->
    <child>
      <object class="GtkLabel" id="mode_status_label">
        <property name="label">Safe</property>
        <style>
          <class name="heading"/>
        </style>
      </object>
    </child>
  </object>
</child>
```

### 2. Update MainWindow Class (`src/hyprbind/ui/main_window.py`)

Add template children and initialize mode manager:

```python
@Gtk.Template(filename=str(_UI_FILE))
class MainWindow(Adw.ApplicationWindow):
    """Main HyprBind application window."""

    __gtype_name__ = "HyprBindMainWindow"

    # Existing template children
    main_content: Gtk.Box = Gtk.Template.Child()
    header_bar: Adw.HeaderBar = Gtk.Template.Child()

    # Add mode manager UI elements
    mode_switch: Gtk.Switch = Gtk.Template.Child()
    mode_status_label: Gtk.Label = Gtk.Template.Child()

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the main window."""
        super().__init__(**kwargs)

        # Initialize ConfigManager
        from hyprbind.core.config_manager import ConfigManager
        self.config_manager = ConfigManager()

        # Initialize Mode Manager
        from hyprbind.core import ModeManager
        self.mode_manager = ModeManager(self.config_manager)

        # Setup mode controls
        self._setup_mode_controls()

        # Rest of initialization...
        self._setup_chezmoi_banner()
        self._setup_tabs()
        self.config_manager.add_observer(self._on_config_changed)
        self._load_config_async()

    def _setup_mode_controls(self) -> None:
        """Setup mode toggle switch and connect signals."""
        # Connect switch toggle signal
        self.mode_switch.connect("notify::active", self._on_mode_switch_toggled)

        # Update initial state
        self._update_mode_ui()

        # Check if Live mode is available
        if not self.mode_manager.is_live_available():
            # Disable Live mode if Hyprland not running
            self.mode_switch.set_sensitive(False)
            self.mode_switch.set_tooltip_text(
                "Live mode unavailable - Hyprland is not running"
            )

    def _on_mode_switch_toggled(self, switch: Gtk.Switch, _pspec: Any) -> None:
        """Handle mode switch toggle."""
        is_active = switch.get_active()

        if is_active:
            # User wants to enable Live mode
            self._show_live_mode_confirmation_dialog()
        else:
            # Switch back to Safe mode
            self.mode_manager.set_mode(Mode.SAFE)
            self._update_mode_ui()

    def _show_live_mode_confirmation_dialog(self) -> None:
        """Show confirmation dialog when enabling Live mode."""
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading("Enable Live Mode?")
        dialog.set_body(
            "Live mode sends changes directly to Hyprland via IPC.\n\n"
            "• Changes are temporary (not saved to file)\n"
            "• Test bindings immediately without reload\n"
            "• Changes persist until HyprBind closes\n\n"
            "Use the Save button to write changes to the config file.\n\n"
            "Continue?"
        )

        dialog.add_response("cancel", "Cancel")
        dialog.add_response("enable", "Enable Live Mode")
        dialog.set_response_appearance("enable", Adw.ResponseAppearance.SUGGESTED)

        dialog.connect("response", self._on_live_mode_confirmation_response)
        dialog.present()

    def _on_live_mode_confirmation_response(
        self, dialog: Adw.MessageDialog, response: str
    ) -> None:
        """Handle Live mode confirmation dialog response."""
        if response == "enable":
            # Try to enable Live mode
            from hyprbind.core import Mode

            if self.mode_manager.set_mode(Mode.LIVE):
                self._update_mode_ui()
                self._show_live_mode_banner()
            else:
                # Failed to enable (Hyprland not running)
                self.mode_switch.set_active(False)
                self._show_error_dialog(
                    "Live Mode Unavailable",
                    "Could not connect to Hyprland. Make sure Hyprland is running."
                )
        else:
            # User cancelled - revert switch
            self.mode_switch.set_active(False)

    def _update_mode_ui(self) -> None:
        """Update UI to reflect current mode."""
        from hyprbind.core import Mode

        current_mode = self.mode_manager.get_mode()

        if current_mode == Mode.SAFE:
            self.mode_status_label.set_text("Safe")
            self.mode_status_label.remove_css_class("success")
            self.mode_status_label.add_css_class("dim-label")
        else:
            self.mode_status_label.set_text("Live")
            self.mode_status_label.remove_css_class("dim-label")
            self.mode_status_label.add_css_class("success")

    def _show_live_mode_banner(self) -> None:
        """Show informational banner when Live mode is active."""
        # This could be an Adw.Banner added to the UI template
        # showing "Live mode active - changes are temporary until saved"
        pass

    def _show_error_dialog(self, heading: str, body: str) -> None:
        """Show error dialog."""
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading(heading)
        dialog.set_body(body)
        dialog.add_response("ok", "OK")
        dialog.present()
```

### 3. Update Editor Tab to Use Mode Manager

Modify the editor tab to use `mode_manager.apply_binding()` instead of calling `config_manager` directly:

```python
# In editor_tab.py

def _on_add_binding_clicked(self, button: Gtk.Button) -> None:
    """Handle add binding button click."""
    # Get mode manager from main window
    mode_manager = self._get_mode_manager()

    # Create binding from dialog
    binding = self._get_binding_from_dialog()

    # Apply based on current mode
    result = mode_manager.apply_binding(binding, "add")

    if result.success:
        # Show success message with mode-specific text
        self._show_success_toast(result.message)
        # Only mark as dirty if in Safe mode
        if mode_manager.get_mode() == Mode.SAFE:
            self._mark_dirty()
    else:
        self._show_error_dialog("Failed to add binding", result.message)

def _get_mode_manager(self) -> ModeManager:
    """Get mode manager from main window."""
    # Access parent window's mode_manager
    main_window = self.get_root()
    return main_window.mode_manager
```

### 4. Add CSS Styling (`data/ui/style.css`)

Add visual styling for mode indicator:

```css
/* Mode indicator styles */
.mode-safe {
    color: @window_fg_color;
}

.mode-live {
    color: @success_color;
    font-weight: bold;
}

/* Success class for Live mode label */
.success {
    color: @success_color;
}
```

## Usage Flow

### Safe Mode (Default)

1. User makes changes in the editor
2. Changes are written to config file
3. User must reload Hyprland (`hyprctl reload`) for changes to take effect
4. Safe for experimentation - can always restore from backup

### Live Mode

1. User toggles mode switch to enable Live mode
2. Confirmation dialog explains behavior
3. User makes changes in the editor
4. Changes are sent immediately via IPC to running Hyprland
5. Changes take effect instantly for testing
6. Changes are NOT saved to file automatically
7. User can save to file with Save button if satisfied
8. Changes revert when HyprBind closes (unless saved)

## Testing Checklist

- [ ] Mode switch toggles between Safe and Live
- [ ] Confirmation dialog appears when enabling Live mode
- [ ] Mode indicator updates correctly
- [ ] Live mode disabled when Hyprland not running
- [ ] Bindings apply via file in Safe mode
- [ ] Bindings apply via IPC in Live mode
- [ ] Live mode changes revert when not saved
- [ ] Save button writes Live mode changes to file
- [ ] Mode persists during session
- [ ] Error handling for IPC failures

## API Reference

See `src/hyprbind/core/mode_manager.py` for complete API documentation:

- `Mode.SAFE` - File-only mode
- `Mode.LIVE` - IPC testing mode
- `ModeManager.get_mode()` - Get current mode
- `ModeManager.set_mode(mode)` - Change mode
- `ModeManager.is_live_available()` - Check if Live mode available
- `ModeManager.apply_binding(binding, action)` - Apply binding based on mode
