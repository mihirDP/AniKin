"""
theme.py
Centralized theme and stylesheet for AniKin.

All colors, fonts, spacing, and styling are defined here so the UI
has a consistent, professional look — and so reskinning is a single-file change.

Design goals:
- Dark mode that sits comfortably alongside Maya's default Charcoal theme
- Distinct accent color (amber) so AniKin controls are instantly identifiable
- Compact: this is a toolbar, not a dialog — every pixel counts

v0.5.0 — Full redesign with new color tokens, amber accent, semantic
color system, and updated button hierarchy per AniKin Brand Stance PRD.
"""

import os

# ──────────────────────────────────────────────────────────────
# Theme Definitions
# ──────────────────────────────────────────────────────────────

THEMES = {
    "Amber": {
        "bg_base": "#0d0f10",
        "bg_surface": "#161a1d",
        "bg_elevated": "#1e2428",
        "bg_active": "#2a3038",
        "bg_input": "#111315",
        
        "border": "#2a3038",
        "border_light": "#3a4048",
        
        "text": "#f0f2f4",
        "text_secondary": "#8b9299",
        "text_disabled": "#4a5260",
        
        "accent": "#d4860a",
        "accent_muted": "rgba(212, 134, 10, 0.15)",
        "accent_hover_bg": "rgba(212, 134, 10, 0.25)",
        "accent_pressed_bg": "rgba(212, 134, 10, 0.35)",
        
        "danger": "#c0392b",
        "danger_muted": "rgba(192, 57, 43, 0.15)",
        "danger_hover_bg": "rgba(192, 57, 43, 0.25)",
        
        "separator": "#2a3038"
    },
    "MayaBlue": {
        "bg_base": "#2b2b2b",
        "bg_surface": "#323232",
        "bg_elevated": "#3d3d3d",
        "bg_active": "#4a4a4a",
        "bg_input": "#1e1e1e",
        
        "border": "#1f1f1f",
        "border_light": "#4a4a4a",
        
        "text": "#e0e0e0",
        "text_secondary": "#aaaaaa",
        "text_disabled": "#666666",
        
        "accent": "#5285a6",
        "accent_muted": "rgba(82, 133, 166, 0.15)",
        "accent_hover_bg": "rgba(82, 133, 166, 0.25)",
        "accent_pressed_bg": "rgba(82, 133, 166, 0.35)",
        
        "danger": "#e74c3c",
        "danger_muted": "rgba(231, 76, 60, 0.15)",
        "danger_hover_bg": "rgba(231, 76, 60, 0.25)",
        
        "separator": "#1f1f1f"
    },
    "Crimson": {
        "bg_base": "#0f0d0d",
        "bg_surface": "#1d1616",
        "bg_elevated": "#281e1e",
        "bg_active": "#382a2a",
        "bg_input": "#151111",
        "border": "#382a2a",
        "border_light": "#483a3a",
        "text": "#f4f0f0",
        "text_secondary": "#998b8b",
        "text_disabled": "#604a4a",
        "accent": "#d93838",
        "accent_muted": "rgba(217, 56, 56, 0.15)",
        "accent_hover_bg": "rgba(217, 56, 56, 0.25)",
        "accent_pressed_bg": "rgba(217, 56, 56, 0.35)",
        "danger": "#e74c3c",
        "danger_muted": "rgba(231, 76, 60, 0.15)",
        "danger_hover_bg": "rgba(231, 76, 60, 0.25)",
        "separator": "#382a2a"
    },
    "Emerald": {
        "bg_base": "#0d100d",
        "bg_surface": "#161d16",
        "bg_elevated": "#1e281e",
        "bg_active": "#2a382a",
        "bg_input": "#111511",
        "border": "#2a382a",
        "border_light": "#3a483a",
        "text": "#f0f4f0",
        "text_secondary": "#8b998b",
        "text_disabled": "#4a604a",
        "accent": "#2eab5c",
        "accent_muted": "rgba(46, 171, 92, 0.15)",
        "accent_hover_bg": "rgba(46, 171, 92, 0.25)",
        "accent_pressed_bg": "rgba(46, 171, 92, 0.35)",
        "danger": "#e74c3c",
        "danger_muted": "rgba(231, 76, 60, 0.15)",
        "danger_hover_bg": "rgba(231, 76, 60, 0.25)",
        "separator": "#2a382a"
    },
    "Amethyst": {
        "bg_base": "#100d12",
        "bg_surface": "#1a161d",
        "bg_elevated": "#251e28",
        "bg_active": "#352a38",
        "bg_input": "#131115",
        "border": "#352a38",
        "border_light": "#453a48",
        "text": "#f2f0f4",
        "text_secondary": "#928b99",
        "text_disabled": "#564a60",
        "accent": "#9b59b6",
        "accent_muted": "rgba(155, 89, 182, 0.15)",
        "accent_hover_bg": "rgba(155, 89, 182, 0.25)",
        "accent_pressed_bg": "rgba(155, 89, 182, 0.35)",
        "danger": "#e74c3c",
        "danger_muted": "rgba(231, 76, 60, 0.15)",
        "danger_hover_bg": "rgba(231, 76, 60, 0.25)",
        "separator": "#352a38"
    }
}

# Compatibility aliases for legacy code
BACKGROUND_MAIN = THEMES["Amber"]["bg_base"]
BACKGROUND_SECTION = THEMES["Amber"]["bg_surface"]
BACKGROUND_INPUT = THEMES["Amber"]["bg_input"]
BACKGROUND_HOVER = THEMES["Amber"]["bg_elevated"]
BACKGROUND_PRESSED = THEMES["Amber"]["bg_active"]
SEPARATOR = THEMES["Amber"]["separator"]
ACCENT = THEMES["Amber"]["accent"]
TEXT_PRIMARY = THEMES["Amber"]["text"]
TEXT_SECONDARY = THEMES["Amber"]["text_secondary"]
BORDER = THEMES["Amber"]["border"]

def get_theme_colors(theme_name=None):
    custom_theme = None
    if not theme_name or theme_name not in THEMES:
        # Fallback to loading from settings
        try:
            from anikin.core.settings import load_settings
            cfg = load_settings()
            theme_name = cfg.get("theme", "Amber")
            custom_theme = cfg.get("custom_theme")
        except ImportError:
            theme_name = "Amber"
            
    if theme_name == "Custom" and custom_theme:
        return custom_theme

    if theme_name not in THEMES:
        theme_name = "Amber"
        
    return THEMES[theme_name]

# ──────────────────────────────────────────────────────────────
# Stylesheet Generator
# ──────────────────────────────────────────────────────────────

def get_stylesheet(theme_name=None):
    colors = get_theme_colors(theme_name)
    
    return """
    /* ── Global ────────────────────────────────────────────────── */
    QWidget#AniKinToolbar {{
        background-color: {bg_base};
        border-top: 1px solid {border};
        font-family: "Segoe UI", "Inter", "Roboto", sans-serif;
        font-size: 11px;
        color: {text};
    }}

    /* ── Push Buttons (default) ──────────────────────────────── */
    QPushButton {{
        background-color: {bg_surface};
        color: {text};
        border: 1px solid transparent;
        border-radius: 5px;
        padding: 3px;
    }}
    QPushButton:hover {{
        background-color: {bg_elevated};
        border-color: {border};
    }}
    QPushButton:pressed {{
        background-color: {bg_active};
    }}
    QPushButton:disabled {{
        color: {text_disabled};
        background-color: {bg_base};
    }}

    /* ── Accent buttons (primary actions) ─────────────────────── */
    QPushButton[accent="true"] {{
        background-color: {accent_muted};
        color: #ffffff;
        border: 1px solid {accent}44;
        font-weight: bold;
    }}
    QPushButton[accent="true"]:hover {{
        background-color: {accent}30;
        border-color: {accent}80;
    }}
    QPushButton[accent="true"]:pressed {{
        background-color: {accent}50;
    }}

    /* ── Danger buttons ──────────────────────────────────────── */
    QPushButton[danger="true"] {{
        background-color: {bg_surface};
        border: 1px solid transparent;
    }}
    QPushButton[danger="true"]:hover {{
        background-color: {danger}18;
        border-color: {danger}55;
    }}

    /* ── Toggle Button (checkable / checked) ─────────────────── */
    QPushButton:checked {{
        background-color: {accent_muted};
        border-color: {accent};
    }}
    QPushButton:checked:hover {{
        background-color: {accent_hover_bg};
    }}

    /* ── Tool Buttons (clean, flat, borderless) ───────────────── */
    ToolButton {{
        background-color: transparent;
        border: none;
        border-radius: 5px;
        padding: 2px;
    }}
    ToolButton:hover {{
        background-color: {bg_elevated};
    }}
    ToolButton:pressed {{
        background-color: {bg_active};
    }}
    ToolButton[accent="true"] {{
        border: 1px solid {accent_pressed_bg};
        background-color: {accent_muted};
    }}
    ToolButton[accent="true"]:hover {{
        border-color: {accent};
        background-color: {accent_hover_bg};
    }}
    ToolButton[accent="true"]:pressed {{
        border-color: {accent};
        background-color: {accent_pressed_bg};
    }}
    
    ToolButton[danger="true"] {{
        background-color: transparent;
        border: none;
    }}
    ToolButton[danger="true"]:hover {{
        background-color: {danger_hover_bg};
        border: 1px solid {danger_muted};
    }}

    /* ── Separators ───────────────────────────────────────────── */
    QFrame[frameShape="5"] {{
        color: {separator};
        background-color: {separator};
        max-width: 1px;
        min-width: 1px;
    }}

    /* ── Sliders ──────────────────────────────────────────────── */
    QSlider::groove:horizontal {{
        border: none;
        height: 5px;
        background: {bg_active};
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        background: {accent};
        border: 1px solid {border_light};
        width: 12px;
        height: 12px;
        margin: -4px 0;
        border-radius: 6px;
    }}
    QSlider::handle:horizontal:hover {{
        background: {text};
    }}
    QSlider::sub-page:horizontal {{
        background: {accent_pressed_bg};
        border-radius: 2px;
    }}

    /* ── Spin Boxes ───────────────────────────────────────────── */
    QSpinBox, QDoubleSpinBox {{
        background-color: {bg_input};
        color: {text};
        border: 1px solid {border};
        border-radius: 3px;
        padding: 2px 4px;
        min-height: 20px;
    }}

    /* ── Labels ───────────────────────────────────────────────── */
    QLabel {{
        color: {text_secondary};
        font-size: 10px;
    }}
    QLabel[header="true"] {{
        color: {accent};
        font-size: 10px;
        font-weight: bold;
        text-transform: uppercase;
    }}

    /* ── Logo Label ───────────────────────────────────────────── */
    QLabel#AniKinLogo {{
        color: {accent};
        font-weight: 700;
        font-size: 11px;
        letter-spacing: 1px;
        padding: 0 6px;
    }}

    /* ── Line Edit (text fields) ──────────────────────────────── */
    QLineEdit {{
        background-color: {bg_input};
        color: {text};
        border: 1px solid {border};
        border-radius: 3px;
        padding: 3px 6px;
        min-height: 20px;
    }}

    /* ── Tooltips ─────────────────────────────────────────────── */
    QToolTip {{
        background-color: {bg_surface};
        color: {text};
        border: 1px solid {border};
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 11px;
    }}

    /* ── Scroll Area ──────────────────────────────────────────── */
    QScrollArea {{
        border: none;
        background-color: transparent;
    }}

    /* ── Context Menus ────────────────────────────────────────── */
    QMenu {{
        background-color: {bg_surface};
        color: {text};
        border: 1px solid {border};
        padding: 2px;
    }}
    QMenu::item {{
        padding: 4px 18px 4px 18px;
        background-color: transparent;
    }}
    QMenu::item:selected {{
        background-color: {accent}30;
        color: #ffffff;
    }}
    QMenu::separator {{
        height: 1px;
        background-color: {border};
        margin: 4px 0px;
    }}

    /* ── Tab Widget ───────────────────────────────────────────── */
    QTabWidget::pane {{
        border: 1px solid {border};
        background-color: {bg_base};
    }}
    QTabBar::tab {{
        background-color: {bg_surface};
        color: {text_secondary};
        border: 1px solid {border};
        border-bottom-color: transparent;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        padding: 5px 12px;
    }}
    QTabBar::tab:selected, QTabBar::tab:hover {{
        background-color: {bg_base};
        color: {text};
    }}
    QTabBar::tab:selected {{
        border-color: {border};
        border-bottom-color: transparent;
    }}

    /* ── Check Boxes ──────────────────────────────────────────── */
    QCheckBox {{
        color: {text};
        spacing: 5px;
    }}
    QCheckBox::indicator {{
        width: 13px;
        height: 13px;
        border: 1px solid {border};
        border-radius: 2px;
        background-color: {bg_input};
    }}
    QCheckBox::indicator:checked {{
        background-color: {accent};
        border-color: {border_light};
    }}

    /* ── Combo Boxes ──────────────────────────────────────────── */
    QComboBox {{
        background-color: {bg_input};
        color: {text};
        border: 1px solid {border};
        border-radius: 3px;
        padding: 3px 6px;
        min-height: 20px;
    }}
    QComboBox::drop-down {{
        border-left: 1px solid {border};
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 16px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {bg_surface};
        color: {text};
        selection-background-color: {accent_hover_bg};
        border: 1px solid {border};
    }}

    /* ── List Widget ──────────────────────────────────────────── */
    QListWidget {{
        background-color: {bg_input};
        color: {text};
        border: 1px solid {border};
        border-radius: 3px;
    }}
    QListWidget::item:selected {{
        background-color: {accent_hover_bg};
        color: {text};
    }}
    """.format(**colors)

STYLESHEET = get_stylesheet()
