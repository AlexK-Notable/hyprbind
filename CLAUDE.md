# HyprBind - Development Guide for Claude Code

This document provides guidance for Claude Code when working on the HyprBind project.

## Project Overview

**HyprBind** is a GTK4-based GUI configurator for Hyprland keybindings. It provides:
- Visual keybinding editor with conflict detection
- Community profile import from GitHub
- Safe/Live mode for testing bindings
- Dynamic theming with Wallust integration
- Export to multiple formats
- Comprehensive reference library

**Tech Stack:**
- Python 3.11+
- GTK4 + Libadwaita (PyGObject)
- Hyprland IPC
- Chezmoi integration for backups

## Project Structure

```
hyprbind/
├── src/hyprbind/          # Main application code
│   ├── ui/                # GTK4 interface components
│   ├── core/              # Business logic (parser, config manager)
│   ├── parsers/           # Hyprland config parsing
│   ├── ipc/               # Hyprland socket communication
│   ├── utils/             # Backup, export, GitHub fetcher
│   └── themes/            # Wallust integration
├── data/                  # Reference data, UI files, icons
├── tests/                 # Test suite
├── project-docs/          # All project documentation
│   ├── design/           # Design documents
│   ├── api/              # API documentation
│   ├── features/         # Feature documentation
│   └── plans/            # Implementation plans
└── CLAUDE.md             # This file
```

## Documentation Requirements

### File Organization
- **All documentation** must be in `project-docs/` directory
- Design docs: `project-docs/design/`
- Implementation plans: `project-docs/plans/`
- API docs: `project-docs/api/`
- Feature writeups: `project-docs/features/`

### Documentation Workflow
1. **After major feature completion**, invoke documentation agent:
   - Use `code-documentation:docs-architect` for comprehensive writeups
   - Use `code-documentation:tutorial-engineer` for user-facing guides
2. Documentation should cover: purpose, architecture, usage, examples
3. Keep docs in sync with code changes

## Development Workflow

### Mandatory Process
1. **Planning Phase**
   - Use `superpowers:writing-plans` skill
   - Create detailed implementation plan in `project-docs/plans/`
   - Break into bite-sized tasks with verification criteria

2. **Git Worktree Setup**
   - Use `superpowers:using-git-worktrees` skill
   - Isolated workspace for feature development
   - Easy rollback if needed

3. **Test-Driven Development**
   - Use `superpowers:test-driven-development` skill
   - Write failing test → implement → refactor
   - Critical for parser and conflict detection reliability

4. **Parallel Development**
   - Use `superpowers:subagent-driven-development` skill
   - Dispatch independent modules to separate agents
   - Code review between tasks

5. **Verification**
   - Use `superpowers:verification-before-completion` skill
   - Run actual tests, verify against requirements
   - Test with user's real keybinds.conf

6. **Code Review**
   - Use `superpowers:requesting-code-review` skill
   - Review against design document
   - Security and edge case validation

7. **Finishing**
   - Use `superpowers:finishing-a-development-branch` skill
   - Merge, PR, or cleanup decisions
   - Documentation agent invocation

## Essential Skills for This Project

### Superpowers Skills

#### Development Workflow
- **superpowers:writing-plans** - Create detailed implementation plans
- **superpowers:using-git-worktrees** - Isolated development workspace
- **superpowers:test-driven-development** - TDD methodology (critical for parser)
- **superpowers:subagent-driven-development** - Parallel development of independent modules
- **superpowers:finishing-a-development-branch** - Complete feature integration

#### Quality & Debugging
- **superpowers:verification-before-completion** - Verify before claiming completion
- **superpowers:requesting-code-review** - Review against plan and standards
- **superpowers:systematic-debugging** - Structured debugging approach
- **superpowers:receiving-code-review** - Handle review feedback properly

#### Development Practices
- **superpowers:brainstorming** - Design refinement (already used)
- **elements-of-style:writing-clearly-and-concisely** - Documentation quality

### Code Documentation Agents

Use after major feature completion:

#### docs-architect
Creates comprehensive technical documentation from code.
```
Use when: Major feature complete, need architecture docs
Task tool: subagent_type="code-documentation:docs-architect"
```

#### tutorial-engineer
Creates step-by-step tutorials and user guides.
```
Use when: User-facing features need explanation
Task tool: subagent_type="code-documentation:tutorial-engineer"
```

#### code-reviewer
Elite code review for quality, security, performance.
```
Use when: Before merging major features
Task tool: subagent_type="code-documentation:code-reviewer"
```

### Debugging & Testing Agents

#### debugger
Specialized debugging for errors and test failures.
```
Use when: Encountering bugs, test failures
Task tool: subagent_type="debugging-toolkit:debugger"
```

#### test-automator
Master test automation with modern frameworks.
```
Use when: Need comprehensive test coverage
Task tool: subagent_type="unit-testing:test-automator"
```

## MCP Servers for This Project

### Essential MCP Servers

#### context7
Up-to-date documentation for libraries and frameworks.
```
Primary use: GTK4, Python, PyGObject documentation
Tools: resolve-library-id, get-library-docs
Example: Get GTK4 docs for specific widgets
```

#### augments
Framework documentation and reference.
```
Primary use: Python framework best practices
Tools: search_frameworks, get_framework_docs
Example: Look up Python patterns and conventions
```

#### desktop-commander
File operations, process management, system tasks.
```
Primary use: File ops during development, testing scripts
Tools: read_file, write_file, list_directory, start_process
CRITICAL: Use for ALL local file operations
```

#### in-memoria
Codebase intelligence and pattern learning.
```
Primary use: As codebase grows, understand architecture
Tools: auto_learn_if_needed, predict_coding_approach, get_project_blueprint
Example: Route to correct files for features
```

#### ai-distiller
Extract code structure and API signatures.
```
Primary use: Analyze existing Hyprland configs, understand code structure
Tools: distill_file, distill_directory, aid_generate_docs
Example: Analyze user's keybinds.conf structure
```

### Supporting MCP Servers

#### mcp-mermaid
Create technical diagrams (flowcharts, sequence diagrams).
```
Use when: Documenting architecture, data flow
Tools: generate_mermaid_diagram, generate_mermaid_diagrams_batch
```

#### clear-thought
Structured reasoning for complex problems.
```
Use when: Solving complex design decisions
Tools: clear_thought with operation types
```

#### npm-sentinel (if needed for web components)
NPM package analysis and security.
```
Use when: Evaluating JavaScript dependencies (if any)
Tools: npmSearch, npmCompare, npmVulnerabilities
```

## Development Priorities

### Phase 1: Foundation (Parser & Core)
**Focus:** Reliable config parsing, data models
**Skills:** test-driven-development
**MCP:** context7 (Python patterns), ai-distiller (analyze existing configs)
**Tests:** Unit tests for every parse case

### Phase 2: Core Logic (Config Manager, Conflict Detection)
**Focus:** Business logic without UI
**Skills:** test-driven-development, systematic-debugging
**MCP:** desktop-commander (test with real files)
**Tests:** Integration tests with sample configs

### Phase 3: UI Shell (GTK4 Basic Interface)
**Focus:** Main window, basic navigation
**Skills:** subagent-driven-development (UI components parallel)
**MCP:** context7 (GTK4 docs), augments (GTK patterns)
**Tests:** UI component tests

### Phase 4: Editor & Tabs (Core Features)
**Focus:** Binding editor, reference library, community import
**Skills:** subagent-driven-development (parallel tab development)
**MCP:** context7, desktop-commander
**Tests:** End-to-end workflows

### Phase 5: Export & Polish (Wallust, Export System)
**Focus:** Theme integration, export formats
**Skills:** verification-before-completion
**MCP:** desktop-commander (test exports)
**Tests:** Export format validation

### Phase 6: Documentation & Release
**Focus:** Comprehensive docs, packaging
**Skills:** finishing-a-development-branch, elements-of-style
**Agents:** docs-architect, tutorial-engineer
**Deliverable:** Complete project documentation

## Coding Standards

### Python Style
- Follow PEP 8
- Type hints for all functions
- Docstrings for all public APIs (Google style)
- Maximum line length: 100 characters

### GTK4 Patterns
- Use Libadwaita widgets where appropriate
- Separate UI definition (Builder XML) from logic
- Signal handlers clearly named: `on_{widget}_{signal}`
- Use data binding where possible

### Testing Requirements
- Minimum 80% code coverage
- Unit tests for all parsers and core logic
- Integration tests for config operations
- UI tests for critical workflows
- Test with user's actual keybinds.conf

### Documentation Requirements
- Every module has docstring explaining purpose
- Complex functions have usage examples
- Public API fully documented in `project-docs/api/`
- User-facing features have tutorials in `project-docs/features/`

## Security Considerations

### Config File Operations
- Always validate before writing
- Create backups before modifications
- Use atomic writes (write to temp, then rename)
- Preserve file permissions

### Hyprland IPC
- Validate all commands before sending
- Handle socket errors gracefully
- Timeout for all IPC operations
- Never execute arbitrary user input directly

### GitHub Import
- Validate URLs before fetching
- Sanitize imported content
- Preview before applying
- Warn on potentially dangerous commands

## Key Design Decisions

### Why GTK4 + Python?
- Native Wayland support
- Matches user's CachyOS aesthetic
- Rapid development
- Excellent theming integration

### Why Hybrid Key Capture?
- Interactive capture: fast, intuitive
- Manual form: precision for power users
- Accommodates different workflows

### Why Dual Mode (Safe/Live)?
- Safe: Preview changes, good for learning
- Live: Instant feedback via IPC, good for iteration
- User choice respects different working styles

### Why Community Profiles?
- Leverage community knowledge
- More valuable than static templates
- Encourages sharing and discovery
- GitHub as universal format

### Why Chezmoi Integration?
- User already has backup system
- No redundant backup mechanisms
- Respects existing workflow
- Dotfile management best practice

## Common Patterns

### Config File Operations
```python
# Always use ConfigManager, never direct file I/O
config = ConfigManager.load()
config.add_binding(binding)
config.save()  # Handles backup automatically
```

### Hyprland IPC
```python
# Use IPC wrapper for all operations
from hyprbind.ipc import HyprlandIPC

ipc = HyprlandIPC()
if ipc.test_binding(binding):
    ipc.apply_binding(binding)
```

### Conflict Detection
```python
# Check before operations
conflicts = conflict_detector.check(new_binding)
if conflicts:
    resolution = show_conflict_dialog(conflicts)
    handle_resolution(resolution)
```

### Backup Creation
```python
# Automatic via BackupManager
backup_manager.create_snapshot("Before adding new binding")
# Integrates with chezmoi if enabled
```

## Testing Strategy

### Unit Tests
- Every parser function
- Conflict detection logic
- Export format generation
- Variable resolution

### Integration Tests
- Full config read → modify → write
- Backup and restore
- GitHub profile import
- Hyprland IPC communication

### UI Tests
- Key capture workflow
- Conflict dialog interaction
- Tab navigation
- Export dialog

### Manual Testing Checklist
- Load user's actual keybinds.conf
- Create intentional conflicts
- Test Safe vs Live mode switching
- Import community profile from real GitHub URL
- Export to all formats
- Verify Wallust theme updates

## Troubleshooting

### Parser Issues
- Use ai-distiller to analyze problematic configs
- Add test cases for edge cases
- Validate against Hyprland wiki examples

### UI Issues
- Check context7 for GTK4 widget documentation
- Verify Libadwaita version compatibility
- Test with different themes

### IPC Issues
- Verify Hyprland socket location
- Check permissions on socket
- Test with `hyprctl` directly first

## Resources

### External Documentation
- Hyprland Wiki: https://wiki.hyprland.org/
- GTK4 Docs: https://docs.gtk.org/gtk4/
- PyGObject Guide: https://pygobject.readthedocs.io/
- Libadwaita: https://gnome.pages.gitlab.gnome.org/libadwaita/

### MCP Server Access
- Use context7 for up-to-date library docs
- Use augments for framework patterns
- Use desktop-commander for file operations

### Skills Access
- All superpowers skills via Skill tool
- Documentation agents via Task tool
- Testing agents via Task tool

## Notes for Claude

- **Always verify** before claiming completion (verification-before-completion skill)
- **Use TodoWrite** to track progress through implementation
- **Invoke documentation agents** after major features complete
- **Test with real user config** before marking features done
- **Keep all docs** in project-docs/ directory
- **Use git worktrees** for isolated feature development
- **Apply TDD rigorously** for parser and core logic
- **Dispatch parallel work** to subagents when appropriate

---

**Last Updated:** 2025-11-12
**Project Status:** Initial Setup
**Next Phase:** Write implementation plan
