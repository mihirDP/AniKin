# Contributing to AniKin

Thank you for your interest in contributing! AniKin is a GPLv3-licensed project, and all contributions must be compatible with this license.

## Ground Rules

1. **Clean-room only.** Never reference, decompile, or copy code from any commercial animation tool. If you're unsure whether something is "too close," default to not doing it.
2. **Every line of code** you submit must be either your original work or sourced from a license-compatible (MIT/BSD/LGPL/GPL) codebase with proper attribution.
3. **Original assets only.** Icons, artwork, and UI layouts must be original — no mimicry of any commercial tool's branding.

## How to Contribute

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-tool`
3. Write your code with clear docstrings
4. Test in at least one Maya version (ideally both a PySide2 and PySide6 version)
5. Submit a Pull Request with a clear description

## Adding a New Tool

AniKin is modular — each tool is a standalone Python module in `scripts/anikin/tools/`.

1. Create `scripts/anikin/tools/your_tool.py`
2. Use `anikin.core.undo.UndoChunk` for undo support
3. Use `anikin.core.selection` for selection utilities
4. Wire it into the UI by adding a button in `scripts/anikin/ui/main_window.py`

## Code Style

- Python 2/3 compatible (Maya 2022 uses Python 3.7+)
- Use `maya.cmds` for general operations
- Use `OpenMaya` 2.0 API for performance-critical paths
- No `pymel` in hot paths
- Clear docstrings on all public functions

## License

By contributing, you agree that your contributions will be licensed under GPLv3.
