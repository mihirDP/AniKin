"""
AniKin — Open-Source Animator's Toolkit for Maya
Copyright (C) 2026 Mihir Patil
License: GNU GPLv3

A modular, dockable animation productivity toolkit.
Each tool is an independent, loadable component that registers itself
into the main panel via the module loader interface.
"""

__version__ = "0.5.0"
__author__ = "Mihir Patil"
__license__ = "GPL-3.0"


def launch():
    """
    Main entry point. Call this from Maya's Script Editor:
        import anikin
        anikin.launch()
    """
    from anikin.ui.main_window import show_window
    show_window()


def reload_and_launch():
    """
    Development helper. Deep-reloads all AniKin modules then launches.
    Use during development to pick up code changes without restarting Maya.

        import anikin
        anikin.reload_and_launch()
    """
    import sys
    # Purge all cached anikin modules so importlib reimports fresh code
    modules_to_remove = [key for key in sys.modules if key.startswith("anikin")]
    for mod_key in modules_to_remove:
        del sys.modules[mod_key]

    # Re-import and launch
    from anikin.ui.main_window import show_window
    show_window()
