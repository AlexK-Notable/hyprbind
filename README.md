# HyprBind

**Stop editing keybindings in a text file like it's 1995.**

You know the drill. Open `hyprland.conf`, scroll through 200 lines of bindings, try to remember if `SUPER + SHIFT + E` is already taken, make your change, reload, realize you just broke three other bindings because of a conflict you didn't see. Rinse, repeat, rage.

HyprBind fixes this. It's a proper visual editor for Hyprland keybindings with conflict detection, live preview, and the ability to actually *see* what you're doing. Think of it as what Hyprland config editing should have been from the start.

## Why This Exists

| Problem | How We Solve It |
|---------|-----------------|
| "I can't remember what's already bound" | **Conflict detection** - warns before you create overlaps |
| "I broke my config and can't get back" | **Chezmoi integration** - automatic backups, easy rollback |
| "I want to try a binding without committing" | **Safe Mode** - preview changes before applying |
| "Reloading config is slow iteration" | **Live Mode** - instant feedback via Hyprland IPC |
| "I want to see how others set things up" | **Community profiles** - import configs from GitHub |
| "My theme changes and bindings look wrong" | **Wallust integration** - theming that matches your wallpaper |

## What Makes It Different

- **Actually visual**: See all your bindings at once, not buried in a config file
- **Safe by default**: Preview mode lets you experiment without breaking things
- **Instant when you want it**: Live mode for rapid iteration via IPC
- **Respects your workflow**: Integrates with Chezmoi, doesn't reinvent backup
- **Community-powered**: Import and share binding profiles from GitHub

---

## Features

- **Visual Keybinding Editor** - Edit bindings with conflict detection
- **Community Profiles** - Import keybinding configs from GitHub
- **Safe/Live Mode** - Test bindings safely or apply instantly via IPC
- **Wallust Integration** - Dynamic theming that matches your wallpaper
- **Multi-format Export** - Export to various config formats
- **Reference Library** - Built-in documentation for Hyprland dispatchers and commands

## Tech Stack

- Python 3.11+
- GTK4 + Libadwaita (PyGObject)
- Hyprland IPC socket communication
- Chezmoi integration for config backups

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/hyprbind
cd hyprbind

# Install dependencies (Arch-based)
sudo pacman -S python-gobject gtk4 libadwaita

# Install Python package
pip install -e .
```

## Usage

```bash
# Run the application
hyprbind

# Or run directly
python -m hyprbind
```

## Project Structure

```
hyprbind/
├── src/hyprbind/
│   ├── core/           # Config manager, models
│   ├── parsers/        # Hyprland config parsing
│   ├── ipc/            # Hyprland socket communication
│   ├── ui/             # GTK4 interface components
│   ├── integrations/   # Chezmoi, GitHub
│   ├── theming/        # Wallust integration
│   └── export/         # Export format handlers
├── data/               # Reference data, UI files, icons
├── tests/              # Test suite
└── project-docs/       # Design and API documentation
```

## Modes

### Safe Mode
Preview changes before applying. Modifications are staged and can be reviewed, then applied or discarded.

### Live Mode
Changes apply immediately via Hyprland IPC. Instant feedback for iterative configuration.

## Keybinding Workflow

1. **Capture** - Press keys or manually specify the binding
2. **Configure** - Set dispatcher, arguments, and options
3. **Validate** - Automatic conflict detection with resolution options
4. **Apply** - Save to config (Safe) or apply via IPC (Live)

## Backup Integration

HyprBind integrates with Chezmoi for automatic config backups:
- Snapshots before modifications
- Easy rollback to previous states
- Respects your existing dotfile workflow

## Requirements

- Hyprland (running)
- Python 3.11+
- GTK4 and Libadwaita
- PyGObject

## License

MIT
