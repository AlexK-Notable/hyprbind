# Plan Corrections Index
**Status**: Corrections Applied
**Reference**: See `2025-11-12-plan-review-and-corrections.md` for detailed analysis

---

## Applied Corrections Summary

### Critical Fixes (8 total)
1. ✅ **Task 15** - ConfigWriter submap handling + atomic writes
2. ✅ **Task 9** - Async config loading + observer pattern
3. ✅ **Tasks 9-14** - Direct widget references (no tree traversal)
4. ✅ **Task 9** - Observer pattern in ConfigManager
5. ✅ **Task 11** - BindingDialog as Adw.MessageDialog
6. ✅ **Task 10** - Category grouping in Editor list
7. ✅ **Task 11** - Preserve binding metadata (line numbers)
8. ✅ **Task 9** - Dirty state tracking

### Major Fixes (6 total)
1. ✅ **Task 11** - Category selector in dialog
2. ✅ **Task 11** - Bind type selector
3. ✅ **Task 11** - Input validation
4. ✅ **Task 9** - Loading indicator
5. ⚠️ **Task 12** - Reference data expansion (noted for future)
6. ✅ **Task 9** - Unsaved changes warning

---

## Corrected Task Files

**Core Infrastructure:**
- `task-09-corrected.md` - Tab structure + async loading + observers
- `task-10-corrected.md` - Editor with category grouping
- `task-11-corrected.md` - Complete CRUD dialogs with validation
- `task-15-corrected.md` - ConfigWriter with submap + atomic writes

**Unchanged Tasks:**
- Tasks 12-14: Minor test improvements only
- Tasks 16-24: No corrections needed (architectural decisions sound)

---

## Implementation Order (Corrected)

### Batch 4A: Foundation (Sequential)
- Task 9: Tab structure + ConfigManager enhancements

### Batch 4B: Editor (Sequential)
- Task 10: Binding list with category grouping
- Task 11: CRUD dialogs

### Batch 4C: Display Tabs (Parallel - 3 agents)
- Task 12: Reference tab
- Task 13: Community tab
- Task 14: Cheatsheet tab

### Batch 5: Backend (Mixed)
- Task 15: ConfigWriter (sequential - foundation)
- Tasks 16-19: Parallel after Task 15

### Batch 6: Advanced (Mixed)
- Tasks 20-21: Parallel
- Task 22: After 20-21
- Tasks 23-24: Parallel

---

## Key Architecture Changes

**ConfigManager (Task 9 enhancement):**
```python
class ConfigManager:
    def __init__(self):
        self._observers: List[Callable] = []
        self._dirty = False

    def add_observer(self, callback: Callable) -> None
    def _notify_observers(self) -> None
    def is_dirty(self) -> bool
```

**MainWindow (Task 9):**
```python
class MainWindow(Adw.ApplicationWindow):
    def _setup_tabs(self) -> None:
        # Create tabs with empty config
        # Load async with _load_config_async()

    def _load_config_async(self) -> None:
        # Threading + GLib.idle_add

    def do_close_request(self) -> bool:
        # Check dirty state
```

**ConfigWriter (Task 15):**
```python
class ConfigWriter:
    @staticmethod
    def write_file(config, path):
        # Atomic write with backup
        # Temp file + os.replace()

    @staticmethod
    def generate_content(config):
        # Separate non-submap and submap bindings
        # Proper submap blocks
```

**BindingDialog (Task 11):**
```python
class BindingDialog(Adw.MessageDialog):
    def __init__(self, config_manager, binding, parent):
        # Form as extra_child
        # Response handling

    def _validate_input(self) -> Optional[str]
    def get_binding(self) -> Binding:
        # Preserve metadata from original
```

---

## Next: Read Individual Task Files

For full implementation details, read:
- `/home/komi/repos/hyprbind/worktrees/dev/project-docs/plans/corrected-tasks/task-09.md`
- `/home/komi/repos/hyprbind/worktrees/dev/project-docs/plans/corrected-tasks/task-10.md`
- `/home/komi/repos/hyprbind/worktrees/dev/project-docs/plans/corrected-tasks/task-11.md`
- `/home/komi/repos/hyprbind/worktrees/dev/project-docs/plans/corrected-tasks/task-15.md`

Other tasks (12-14, 16-24) follow original plan with minor test improvements.
