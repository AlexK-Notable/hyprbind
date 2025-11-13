# HyprBind Design Document

**Date:** 2025-11-12
**Status:** Approved
**Authors:** Design collaboration with user

## Executive Summary

HyprBind is a GTK4-based GUI configurator for Hyprland keybindings that provides visual editing, conflict detection, community profile import, and comprehensive reference documentation. The application respects user workflows by integrating with existing tools (chezmoi, Wallust) while adding powerful features like live IPC testing and GitHub profile discovery.

## Goals

### Primary Goals
1. **Eliminate manual config editing errors** - Visual interface with validation
2. **Enable safe experimentation** - Dual mode (Safe/Live) with automatic backups
3. **Accelerate keybinding discovery** - Reference library + community profiles
4. **Maintain config file fidelity** - Perfect round-trip parsing and writing

### Secondary Goals
1. **Beautiful, native experience** - GTK4 + Libadwaita + Wallust theming
2. **Community-driven** - Import/export profiles from GitHub
3. **Educational** - Comprehensive reference library teaches Hyprland features
4. **Flexible workflow** - Hybrid interaction (key capture + manual forms)

## Non-Goals

1. **General Hyprland config management** - Focus only on keybindings, not all Hyprland settings
2. **Cross-platform** - Linux/Wayland only (Hyprland requirement)
3. **Cloud sync** - User handles via chezmoi or git
4. **Plugin system** - Core functionality only for v1.0

## Architecture Overview

### Technology Stack

**Frontend**
- GTK4 with Libadwaita for modern GNOME/Wayland aesthetics
- PyGObject for Python bindings
- GTK Builder for declarative UI

**Backend**
- Python 3.11+ (type hints, dataclasses)
- Custom parser for Hyprland config syntax
- Direct Hyprland IPC via Unix socket
- Requests for GitHub profile fetching

**Integration**
- Chezmoi for dotfile management
- Wallust for dynamic color theming
- Hyprland IPC for live mode testing

### High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│                   GTK4 UI Layer                     │
│  ┌──────────┬──────────┬───────────┬─────────────┐ │
│  │ Editor   │Reference │ Community │ Cheatsheet  │ │
│  │   Tab    │   Tab    │    Tab    │     Tab     │ │
│  └──────────┴──────────┴───────────┴─────────────┘ │
└─────────────────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────┐
│                  Core Business Logic                │
│  ┌─────────────┬──────────────┬─────────────────┐  │
│  │   Config    │   Conflict   │      Mode       │  │
│  │   Manager   │   Detector   │    Manager      │  │
│  └─────────────┴──────────────┴─────────────────┘  │
└─────────────────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ↓               ↓               ↓
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   Parser    │ │ Hyprland    │ │   Backup    │
│   Layer     │ │    IPC      │ │  Manager    │
└─────────────┘ └─────────────┘ └─────────────┘
         │               │               │
         ↓               ↓               ↓
┌─────────────────────────────────────────────────────┐
│               External Systems                      │
│  keybinds.conf  │  Hyprland  │  chezmoi  │ Wallust │
└─────────────────────────────────────────────────────┘
```

## Data Model

### Core Data Structures

#### Binding
```python
@dataclass
class Binding:
    """Represents a single Hyprland keybinding"""

    type: BindType  # BINDD, BIND, BINDEL, BINDM
    modifiers: List[str]  # ['$mainMod', 'SHIFT']
    key: str  # 'Q' or 'code:191'
    description: str  # For bindd types
    action: str  # 'exec', 'workspace', 'killactive', etc.
    params: str  # Command or parameters
    submap: Optional[str]  # If inside submap
    line_number: int  # Position in file
    category: str  # 'Window Management', 'Workspaces', etc.

    @property
    def display_name(self) -> str:
        """Human-readable keybinding (Super + Q)"""

    def conflicts_with(self, other: 'Binding') -> bool:
        """Check if this binding conflicts with another"""
```

#### Category
```python
@dataclass
class Category:
    """Organizes bindings into groups"""

    name: str
    bindings: List[Binding]
    icon: str  # GTK icon name
    description: str
    collapsed: bool = False
```

#### Config
```python
@dataclass
class Config:
    """Complete Hyprland keybinding configuration"""

    categories: Dict[str, Category]
    variables: Dict[str, str]  # $mainMod, $terminal, etc.
    submaps: Dict[str, List[Binding]]
    file_path: Path
    original_content: str  # For diff generation

    def add_binding(self, binding: Binding) -> None:
        """Add binding with conflict check"""

    def remove_binding(self, binding: Binding) -> None:
        """Remove and track as unbound"""

    def get_conflicts(self, binding: Binding) -> List[Binding]:
        """Find all conflicts with proposed binding"""
```

## Component Design

### 1. Parser Layer (`src/parsers/`)

#### BindingParser
**Responsibility:** Parse Hyprland config syntax into data structures

**Key Methods:**
```python
def parse_file(path: Path) -> Config:
    """Parse keybinds.conf into Config object"""

def parse_line(line: str) -> Optional[Binding]:
    """Parse single binding line"""

def parse_submap(lines: List[str]) -> Tuple[str, List[Binding]]:
    """Parse submap block"""
```

**Parsing Rules:**
- Preserve comments and whitespace structure
- Handle all bind types: `bindd`, `bind`, `bindel`, `bindm`, `bindm`
- Support submaps with proper nesting
- Gracefully handle malformed lines (log warnings, continue parsing)

**Edge Cases:**
- Lines with `code:XXX` keycode format
- Multiple modifiers in different orders
- Empty descriptions in bindd
- Variables in different positions
- Nested submaps (Hyprland supports this)

#### VariableResolver
**Responsibility:** Resolve variable references

**Key Methods:**
```python
def load_variables(config_dir: Path) -> Dict[str, str]:
    """Load from defaults.conf and variables.conf"""

def resolve(value: str, variables: Dict[str, str]) -> str:
    """Replace $variables with actual values"""
```

#### ConfigWriter
**Responsibility:** Generate valid Hyprland config syntax

**Key Methods:**
```python
def write_config(config: Config, path: Path) -> None:
    """Write Config back to file"""

def format_binding(binding: Binding) -> str:
    """Generate proper syntax for binding"""

def preserve_structure(original: str, new: Config) -> str:
    """Maintain comments, spacing, sections"""
```

**Output Requirements:**
- Maintain original file structure
- Preserve comments and section headers
- Valid Hyprland syntax
- Consistent formatting

### 2. Core Logic (`src/core/`)

#### ConfigManager
**Responsibility:** High-level config operations

**Key Methods:**
```python
def load() -> Config:
    """Load current configuration"""

def save(config: Config) -> None:
    """Save with backup"""

def add_binding(binding: Binding) -> Result:
    """Add with conflict check"""

def update_binding(old: Binding, new: Binding) -> Result:
    """Replace binding"""

def delete_binding(binding: Binding) -> None:
    """Remove and track as unbound"""
```

#### ConflictDetector
**Responsibility:** Identify keybinding conflicts

**Conflict Types:**
1. **Exact Match** - Same modifiers + key
2. **Submap Conflict** - Conflict within same submap
3. **Mouse Binding Conflict** - Mouse button conflicts

**Key Methods:**
```python
def check(binding: Binding, config: Config) -> List[Conflict]:
    """Find all conflicts"""

def suggest_alternatives(binding: Binding) -> List[Binding]:
    """Suggest similar but non-conflicting bindings"""
```

**Resolution Options:**
```python
class ConflictResolution(Enum):
    KEEP_ORIGINAL = "keep"
    REPLACE = "replace"
    ALLOW_BOTH = "both"
```

#### ModeManager
**Responsibility:** Manage Safe vs Live mode

**Safe Mode:**
- All changes in-memory only
- Show diff before applying
- Apply button writes to disk + reloads Hyprland

**Live Mode:**
- Changes via Hyprland IPC immediately
- Runtime bindings active instantly
- Save button writes to disk later
- Auto-revert timer option (10s countdown)

**Key Methods:**
```python
def set_mode(mode: Mode) -> None:
    """Switch between Safe and Live"""

def apply_binding(binding: Binding) -> bool:
    """Apply based on current mode"""

def revert_changes() -> None:
    """Discard pending changes"""
```

### 3. IPC Layer (`src/ipc/`)

#### HyprlandIPC
**Responsibility:** Communicate with Hyprland socket

**Key Methods:**
```python
def connect() -> bool:
    """Connect to Hyprland socket"""

def send_command(cmd: str) -> Response:
    """Send hyprctl command"""

def bind_key(binding: Binding) -> bool:
    """Add runtime binding"""

def reload_config() -> bool:
    """Reload Hyprland config"""

def test_binding(binding: Binding) -> bool:
    """Test if binding works"""
```

**Socket Location:**
- `$XDG_RUNTIME_DIR/hypr/$HYPRLAND_INSTANCE_SIGNATURE/.socket.sock`

**Error Handling:**
- Timeout after 5 seconds
- Retry logic for transient failures
- Clear error messages for user

### 4. UI Layer (`src/ui/`)

#### Main Window Layout

**Structure:**
```
┌────────────────────────────────────────────────────┐
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │
│  ┃ HyprBind          [🛡️Safe / ⚡Live]  [☰]  ┃  │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │
│  ┌──────┬──────────┬──────────┬────────────┐      │
│  │Editor│Reference │Community │ Cheatsheet │      │
│  └──────┴──────────┴──────────┴────────────┘      │
│  ┌───────────────────────────────────────────────┐│
│  │                 Tab Content                   ││
│  │                                               ││
│  └───────────────────────────────────────────────┘│
└────────────────────────────────────────────────────┘
```

#### Tab 1: Editor (Three-Panel Dashboard)

```
┌──────────┬────────────────────────┬────────────────┐
│          │                        │                │
│ Category │    Binding List        │ Binding Editor │
│  Tree    │                        │                │
│          │  ┌──────────────────┐  │ [Press Keys]   │
│ 📁Window │  │Super + Q         │  │                │
│ 📁Workspace  │Close window      │  │ Modifiers: [  ]│
│ 📁Media  │  └──────────────────┘  │ Key: [       ] │
│ 📁Wallpaper  │Super + V         │  │                │
│ 📁Screen │  │Toggle floating   │  │ Description:   │
│          │  └──────────────────┘  │ [            ] │
│ [Search] │                        │                │
│          │  [120 bindings total]  │ Action: [exec] │
│          │                        │ Params: [    ] │
│          │                        │                │
│          │                        │ [Save] [Cancel]│
└──────────┴────────────────────────┴────────────────┘
```

**Left Panel:** Category tree (GtkTreeView)
**Center Panel:** Binding list (GtkListBox with custom rows)
**Right Panel:** Binding editor (collapsible)

#### Tab 2: Reference

```
┌────────────────────────────────────────────────────┐
│  [Search: _________________________________] [🔍]  │
├────────────────────────────────────────────────────┤
│                                                    │
│  Quick Actions                                     │
│  ┌──────────────────────────────────────────────┐ │
│  │ Close Window                              [+]│ │
│  │ killactive - Closes active window            │ │
│  │ Suggested: Super + Q                         │ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
│  All Dispatchers                                   │
│  ┌──────────────────────────────────────────────┐ │
│  │ ▸ exec - Execute command                  [+]│ │
│  │ ▸ workspace - Switch workspace            [+]│ │
│  │ ▸ movewindow - Move window to direction  [+]│ │
│  └──────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────┘
```

**Search:** Filters across all actions
**Cards:** Expandable with full documentation
**Add Button:** Quick-add to config

#### Tab 3: Community

```
┌────────────────────────────────────────────────────┐
│  Import from GitHub                                │
│  ┌──────────────────────────────────────────────┐ │
│  │ URL: https://github.com/user/repo/...       │ │
│  │      [Preview]  [Import]                    │ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
│  My Profiles                                       │
│  ┌──────────────────────────────────────────────┐ │
│  │ Gaming Setup           45 bindings    [View]│ │
│  │ github.com/gamer/hypr                       │ │
│  │ Imported: 2025-11-10        [↻] [🗑️]       │ │
│  └──────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────┐ │
│  │ Photographer Config    32 bindings    [View]│ │
│  │ github.com/photo/dots                       │ │
│  │ Imported: 2025-11-08        [↻] [🗑️]       │ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
│  Share Your Config                                 │
│  [Export to GitHub Gist] [Copy Raw URL]           │
└────────────────────────────────────────────────────┘
```

**Import Preview Dialog:**
```
┌────────────────────────────────────────────────────┐
│  Import Preview: Gaming Setup                      │
├────────────────────────────────────────────────────┤
│  Found: 45 bindings                                │
│  Conflicts: 3 (with your current config)           │
│                                                    │
│  ☑ Super + W  →  exec: firefox (conflicts)         │
│  ☑ Super + G  →  gaps off                          │
│  ☑ Super + F  →  fullscreen                        │
│  ☑ ...                                             │
│                                                    │
│  Conflicts:                                        │
│  • Super + W: Currently "Next wallpaper"           │
│                                                    │
│  [Select All] [Deselect All]                       │
│  [Cancel] [Import Selected]                        │
└────────────────────────────────────────────────────┘
```

#### Tab 4: Cheatsheet

```
┌────────────────────────────────────────────────────┐
│  Filters: [All Categories ▾] [All Modifiers ▾]    │
│  Export: [Markdown] [HTML] [JSON] [Native Config] │
├────────────────────────────────────────────────────┤
│  Window Management                                 │
│  ┌────────────┬─────────────────────────────────┐ │
│  │ Super + Q  │ Close window                    │ │
│  │ Super + V  │ Toggle floating                 │ │
│  │ Super + F  │ Fullscreen                      │ │
│  └────────────┴─────────────────────────────────┘ │
│                                                    │
│  Workspaces                                        │
│  ┌────────────┬─────────────────────────────────┐ │
│  │ Super + 1  │ Switch to workspace 1           │ │
│  │ Super + 2  │ Switch to workspace 2           │ │
│  └────────────┴─────────────────────────────────┘ │
└────────────────────────────────────────────────────┘
```

**Export Preview:** Shows formatted output before saving

### 5. Utilities (`src/utils/`)

#### BackupManager
**Responsibility:** Automatic snapshots before changes

**Backup Strategy:**
- Create snapshot before every save
- Location: `~/.local/share/hyprbind/backups/`
- Filename: `keybinds.conf.YYYYMMDD-HHMMSS.bak`
- Metadata: JSON with timestamp, description, file hash
- Retention: Keep last 50 (configurable)

**Chezmoi Integration:**
```python
def sync_to_chezmoi() -> bool:
    """Add config to chezmoi tracking"""
    # chezmoi add ~/.config/hypr/config/keybinds.conf

def commit_to_chezmoi(message: str) -> bool:
    """Commit change to chezmoi repo"""
    # Requires user preference enabled
```

#### GitHubFetcher
**Responsibility:** Fetch community profiles

**Supported URLs:**
- `https://github.com/user/repo/blob/main/path/keybinds.conf`
- `https://raw.githubusercontent.com/user/repo/main/path/keybinds.conf`
- Direct `.conf` file links

**Process:**
1. Validate URL format
2. Convert blob → raw if needed
3. Fetch with timeout (10s)
4. Validate content is Hyprland config
5. Return for preview

#### Exporters

**HyprlandExporter**
- Generates valid `.conf` syntax
- Includes all bind types
- Preserves variable references
- Maintains submaps

**MarkdownExporter**
- Generates tables by category
- Clean formatting for README
- Optional: include descriptions

**HTMLExporter**
- Responsive web page
- Searchable with JavaScript
- Themed with Wallust colors
- Self-contained (no external deps)

**JSONExporter**
- Structured data format
- Includes metadata
- Version information
- Programmatic processing

### 6. Theme Integration (`src/themes/`)

#### WallustIntegration
**Responsibility:** Apply dynamic colors from Wallust

**Color Sources:**
- Read from `~/.config/hypr/config/colors.conf`
- Or parse Wallust TOML output directly

**Extracted Colors:**
```python
@dataclass
class WallustTheme:
    background: str  # #1a1b26
    foreground: str  # #c0caf5
    accent: str      # #7aa2f7
    warning: str     # #e0af68
    error: str       # #f7768e
    success: str     # #9ece6a
```

**Application:**
- Generate GTK CSS dynamically
- Apply to UI elements
- Use in export templates
- File watcher for wallpaper changes

**GTK CSS Generation:**
```css
@define-color accent_color {accent};
@define-color error_color {error};
@define-color warning_color {warning};

.binding-badge {
    background-color: @accent_color;
}

.conflict-warning {
    background-color: @warning_color;
}
```

## User Workflows

### Workflow 1: Edit Existing Binding

1. Launch HyprBind
2. Navigate to binding in category tree
3. Click binding in center panel
4. Editor panel opens on right
5. Modify description or action
6. Click Save
7. Conflict check passes
8. Safe Mode: Click "Apply Changes"
9. Live Mode: Change applies immediately
10. Backup created automatically

### Workflow 2: Add New Binding from Reference

1. Open Reference tab
2. Search "fullscreen"
3. Find "fullscreen" dispatcher
4. Click "+" button
5. Key capture dialog appears
6. Press desired keys (e.g., Super + F11)
7. Conflict check passes
8. Binding added to config
9. Returns to Editor tab showing new binding

### Workflow 3: Import Community Profile

1. Find interesting config on Reddit/GitHub
2. Copy GitHub file URL
3. Open Community tab
4. Paste URL in import field
5. Click "Preview"
6. Preview dialog shows:
   - 45 bindings found
   - 3 conflicts highlighted
   - Conflict details shown
7. Review conflicts, decide resolution
8. Deselect conflicting items or choose to replace
9. Click "Import Selected"
10. Bindings added to config
11. Profile saved in "My Profiles"

### Workflow 4: Resolve Conflict

1. Creating new binding: Super + W
2. Conflict detected: "Super + W" already bound
3. Conflict dialog appears:
   ```
   New: Super + W → exec: firefox
   Existing: Super + W → variety --next
   ```
4. Choose option:
   - Keep Original (cancel)
   - Replace Original (warning shown)
   - Allow Both (last one wins)
5. If Replace chosen:
   - Confirmation toast: "variety --next is no longer bound"
   - [Undo] button available
   - Unbound Actions counter increments
6. New binding saved

### Workflow 5: Export Cheatsheet

1. Open Cheatsheet tab
2. Filter: Category "Window Management"
3. Filter: Modifiers "$mainMod only"
4. Preview shows filtered list
5. Choose export format: "Markdown"
6. Click Export
7. File picker: Choose location
8. Save as `hyprland-keybindings.md`
9. Toast: "Exported successfully"
10. Option: Open file

### Workflow 6: Test in Live Mode

1. Toggle to Live Mode (⚡)
2. Create new binding: Super + T → exec: thunar
3. Binding applies instantly via IPC
4. Test: Press Super + T
5. Thunar opens! ✓
6. Satisfied with test
7. Click "Save Configuration"
8. Writes to keybinds.conf
9. Backup created
10. Chezmoi sync (if enabled)

## Security Considerations

### Input Validation
- **Config parsing:** Reject malformed bindings
- **GitHub URLs:** Whitelist domains (github.com, raw.githubusercontent.com)
- **exec commands:** Display warnings for sudo/rm/dangerous commands
- **File paths:** Validate paths are within expected locations

### Privilege Management
- **No elevated privileges required**
- **User's file permissions respected**
- **Socket access: user's Hyprland socket only**

### Safe Command Execution
- **Never execute user input directly**
- **Validate IPC commands before sending**
- **Timeout all external operations**
- **Sanitize imported configs**

## Error Handling

### Parse Errors
- **Malformed binding:** Log warning, skip line, continue parsing
- **Missing file:** Show error dialog, offer to create default config
- **Invalid syntax:** Highlight problematic lines in UI

### IPC Errors
- **Socket not found:** Graceful degradation (Safe Mode only)
- **Command failed:** Show error, revert binding
- **Timeout:** Retry once, then fail with clear message

### Import Errors
- **Invalid URL:** Show format requirements
- **Network failure:** Retry option, offline mode
- **Parse failure:** Show parse errors, allow manual fixing

### Backup Errors
- **Disk full:** Warn before operation
- **Permission denied:** Show permission requirements
- **Chezmoi unavailable:** Disable chezmoi features only

## Performance Considerations

### File Operations
- **Lazy loading:** Load config on demand, not at startup
- **Incremental parsing:** Parse modified sections only
- **Async I/O:** Non-blocking file operations

### UI Responsiveness
- **Virtual scrolling:** Large binding lists (>1000)
- **Debounced search:** 300ms delay on search input
- **Cached renders:** GTK list box caching

### Memory Management
- **Limit backup retention:** Default 50 snapshots
- **Clear old references:** Proper cleanup on config reload
- **Efficient data structures:** Use dataclasses, not dicts

## Testing Strategy

### Unit Tests
- Parser: All binding types, edge cases
- Conflict detector: All conflict types
- Variable resolver: Nested variables
- Exporters: Each format

### Integration Tests
- Full config round-trip (read → modify → write)
- IPC communication with mock socket
- GitHub import with mock server
- Backup creation and restore

### UI Tests
- Key capture functionality
- Conflict dialog interaction
- Tab navigation
- Export dialog

### Manual Testing
- **Real config:** Load user's actual keybinds.conf
- **Conflict scenarios:** Create intentional conflicts
- **Mode switching:** Safe ↔ Live transition
- **Import:** Real GitHub profiles
- **Export:** Verify all formats
- **Theming:** Test with different Wallust themes

## Future Enhancements (Post-v1.0)

### Phase 2 Features
- **Global keybinding analytics** - Most/least used bindings
- **Advanced submap editor** - Visual flow diagrams
- **Keybinding macros** - Record sequences
- **Profile recommendations** - ML-based suggestions
- **Collaborative profiles** - Community voting/ratings

### Phase 3 Features
- **Full Hyprland config management** - Beyond keybindings
- **Plugin system** - Third-party extensions
- **Cloud sync** - Optional backend service
- **Mobile companion app** - Android cheatsheet viewer

## Success Criteria

### MVP (v0.1.0)
- ✅ Load and parse keybinds.conf
- ✅ Edit bindings with visual interface
- ✅ Conflict detection with resolution
- ✅ Safe mode with backups
- ✅ Export to native config format

### v1.0.0 Release
- ✅ All MVP features
- ✅ Live mode with Hyprland IPC
- ✅ Reference library (curated)
- ✅ Community profile import
- ✅ Export to all formats
- ✅ Wallust theme integration
- ✅ Comprehensive documentation
- ✅ 80%+ test coverage

### User Satisfaction
- Users prefer GUI over manual editing
- Zero config corruption reports
- Active community profile sharing
- Positive feedback on conflict detection

## Conclusion

HyprBind provides a comprehensive, safe, and intuitive way to manage Hyprland keybindings. By combining visual editing, community features, and deep integration with existing tools (chezmoi, Wallust), it respects user workflows while dramatically improving the configuration experience.

The GTK4 + Python stack ensures native performance and beautiful aesthetics, while the dual-mode system (Safe/Live) accommodates both cautious and iterative workflows. The reference library and community profile import democratize Hyprland knowledge, making advanced configurations accessible to all users.

---

**Next Steps:**
1. Write detailed implementation plan
2. Set up git repository and worktree
3. Begin Phase 1: Parser development with TDD
4. Iterate through phases with parallel development
5. Document as features complete
