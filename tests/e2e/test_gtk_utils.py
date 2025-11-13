"""Test GTK event loop utilities."""
import pytest
import gi
import time

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib

from tests.e2e.gtk_utils import (
    wait_for_condition,
    process_pending_events,
    find_widget_by_name,
    simulate_click,
    simulate_text_entry,
)


def test_wait_for_condition_success():
    """Test wait_for_condition succeeds when predicate becomes true."""
    flag = {'value': False}

    def set_flag():
        flag['value'] = True
        return GLib.SOURCE_REMOVE

    GLib.timeout_add(100, set_flag)  # Set flag after 100ms

    result = wait_for_condition(lambda: flag['value'], timeout=1.0)
    assert result is True


def test_wait_for_condition_timeout():
    """Test wait_for_condition raises on timeout."""
    with pytest.raises(TimeoutError):
        wait_for_condition(lambda: False, timeout=0.1)


def test_process_pending_events():
    """Test processing pending GTK events."""
    process_pending_events()  # Should not hang


def test_find_widget_by_name():
    """Test finding widget by name in hierarchy."""
    box = Gtk.Box()
    box.set_name("test_box")

    button = Gtk.Button()
    button.set_name("test_button")
    box.append(button)

    found = find_widget_by_name(box, "test_button")
    assert found == button

    not_found = find_widget_by_name(box, "nonexistent")
    assert not_found is None


def test_simulate_click():
    """Test simulating button click."""
    clicked = {'value': False}

    button = Gtk.Button()
    button.connect("clicked", lambda b: clicked.update({'value': True}))

    simulate_click(button)
    assert clicked['value'] is True


def test_simulate_text_entry():
    """Test simulating text entry."""
    entry = Gtk.Entry()

    simulate_text_entry(entry, "test text")
    assert entry.get_text() == "test text"
