"""
UI Package for AniPose Pro.

NOTE: All imports are DEFERRED (lazy) to prevent circular dependency chains.
The library/ sub-package imports ui/thumbnail_card.py, so we cannot eagerly
import panel.py (which imports library/) at ui/__init__.py load time.
"""


def show_panel():
    """Deferred launcher for AniPose Pro main panel."""
    from .panel import show_panel as _show
    return _show()


__all__ = [
    "show_panel",
]
