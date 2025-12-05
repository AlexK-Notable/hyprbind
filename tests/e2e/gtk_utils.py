"""GTK event loop and widget utilities for E2E tests."""
import time
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib
from typing import Callable, Optional


def wait_for_condition(
    predicate: Callable[[], bool],
    timeout: float = 5.0,
    poll_interval: float = 0.01
) -> bool:
    """Wait for condition while processing GTK events.

    Args:
        predicate: Function that returns True when condition is met
        timeout: Maximum time to wait in seconds
        poll_interval: Time between condition checks in seconds

    Returns:
        True if condition met within timeout

    Raises:
        TimeoutError: If condition not met within timeout
    """
    start = time.time()
    context = GLib.MainContext.default()

    while time.time() - start < timeout:
        if predicate():
            return True

        # Process pending GTK events
        while context.pending():
            context.iteration(False)

        time.sleep(poll_interval)

    raise TimeoutError(f"Condition not met within {timeout}s")


def process_pending_events(max_iterations: int = 100) -> None:
    """Drain GTK event queue.

    Args:
        max_iterations: Maximum number of events to process
    """
    context = GLib.MainContext.default()
    iterations = 0

    while context.pending() and iterations < max_iterations:
        context.iteration(False)
        iterations += 1


def find_widget_by_name(container: Gtk.Widget, name: str) -> Optional[Gtk.Widget]:
    """Recursively find widget by name in widget hierarchy.

    Args:
        container: Container widget to search
        name: Widget name to find

    Returns:
        Widget if found, None otherwise
    """
    if container.get_name() == name:
        return container

    # Check children
    child = container.get_first_child()
    while child:
        result = find_widget_by_name(child, name)
        if result:
            return result
        child = child.get_next_sibling()

    return None


def simulate_click(widget: Gtk.Widget) -> None:
    """Programmatically activate widget.

    Args:
        widget: Widget to activate (Button, Switch, etc.)
    """
    if isinstance(widget, Gtk.Button):
        widget.emit("clicked")
    elif isinstance(widget, Gtk.Switch):
        widget.set_active(not widget.get_active())
    elif isinstance(widget, Gtk.CheckButton):
        widget.set_active(not widget.get_active())

    # Process resulting events
    process_pending_events()


def simulate_text_entry(entry: Gtk.Entry, text: str) -> None:
    """Type text into entry field.

    Args:
        entry: Entry widget
        text: Text to enter
    """
    entry.set_text(text)
    process_pending_events()
