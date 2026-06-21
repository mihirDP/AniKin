"""
theme.py
Centralized theme and stylesheet for AniKin.

All colors, fonts, spacing, and styling are defined here so the UI
has a consistent, professional look — and so reskinning is a single-file change.

Design goals:
- Dark mode that sits comfortably alongside Maya's default Charcoal theme
- Distinct accent color (teal-blue) so AniKin controls are instantly identifiable
- Compact: this is a toolbar, not a dialog — every pixel counts
"""

# ──────────────────────────────────────────────────────────────
# Color palette
# ──────────────────────────────────────────────────────────────
BACKGROUND_MAIN = "#2d2d2d"       # Main panel background
BACKGROUND_SECTION = "#383838"    # Section group background
BACKGROUND_INPUT = "#1e1e1e"      # Text field / slider track
BACKGROUND_HOVER = "#4a4a4a"      # Button hover state
BACKGROUND_PRESSED = "#555555"    # Button pressed state

ACCENT = "#00b4d8"                # Primary accent (teal-blue)
ACCENT_HOVER = "#48cae4"          # Accent hover
ACCENT_PRESSED = "#0096c7"        # Accent pressed
ACCENT_MUTED = "#023e8a"          # Subtle accent for borders

TEXT_PRIMARY = "#e0e0e0"          # Primary text
TEXT_SECONDARY = "#999999"        # Secondary / label text
TEXT_DISABLED = "#555555"         # Disabled state

BORDER = "#1a1a1a"                # General border
BORDER_LIGHT = "#4a4a4a"          # Lighter border for sections
SEPARATOR = "#555555"             # Vertical separator lines

SUCCESS = "#4caf50"               # Green for positive feedback
WARNING = "#ff9800"               # Amber for warnings
ERROR = "#f44336"                 # Red for errors


# ──────────────────────────────────────────────────────────────
# Stylesheet
# ──────────────────────────────────────────────────────────────

STYLESHEET = """
/* ── Global ────────────────────────────────────────────────── */
QWidget#AniKinToolbar {{
    background-color: {bg_main};
    border: 1px solid {border};
    font-family: "Segoe UI", "Inter", "Roboto", sans-serif;
    font-size: 11px;
    color: {text};
}}

/* ── Push Buttons (tool buttons) ──────────────────────────── */
QPushButton {{
    background-color: {bg_section};
    color: {text};
    border: 1px solid {border};
    border-radius: 3px;
    padding: 4px 8px;
    min-height: 22px;
    font-size: 11px;
}}
QPushButton:hover {{
    background-color: {bg_hover};
    border-color: {accent_muted};
}}
QPushButton:pressed {{
    background-color: {bg_pressed};
    border-color: {accent};
}}
QPushButton:disabled {{
    color: {text_disabled};
    background-color: {bg_main};
}}

/* ── Accent buttons (primary actions) ─────────────────────── */
QPushButton[accent="true"] {{
    background-color: {accent};
    color: #ffffff;
    border: 1px solid {accent_pressed};
    font-weight: bold;
}}
QPushButton[accent="true"]:hover {{
    background-color: {accent_hover};
}}
QPushButton[accent="true"]:pressed {{
    background-color: {accent_pressed};
}}

/* ── Sliders ──────────────────────────────────────────────── */
QSlider::groove:horizontal {{
    border: 1px solid {border};
    height: 6px;
    background: {bg_input};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: {accent};
    border: 1px solid {accent_pressed};
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}
QSlider::handle:horizontal:hover {{
    background: {accent_hover};
}}
QSlider::sub-page:horizontal {{
    background: {accent_muted};
    border-radius: 3px;
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

/* ── Line Edit (text fields) ──────────────────────────────── */
QLineEdit {{
    background-color: {bg_input};
    color: {text};
    border: 1px solid {border};
    border-radius: 3px;
    padding: 3px 6px;
    min-height: 20px;
}}

/* ── Separators ───────────────────────────────────────────── */
QFrame[frameShape="5"] {{
    color: {separator};
    max-width: 1px;
}}

/* ── Tooltips ─────────────────────────────────────────────── */
QToolTip {{
    background-color: {bg_section};
    color: {text};
    border: 1px solid {accent_muted};
    padding: 4px 8px;
    border-radius: 3px;
    font-size: 11px;
}}

/* ── Scroll Area ──────────────────────────────────────────── */
QScrollArea {{
    border: none;
    background-color: transparent;
}}

/* ── Context Menus ────────────────────────────────────────── */
QMenu {{
    background-color: {bg_section};
    color: {text};
    border: 1px solid {border};
    padding: 2px;
}}
QMenu::item {{
    padding: 4px 18px 4px 18px;
    background-color: transparent;
}}
QMenu::item:selected {{
    background-color: {accent_muted};
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
    background-color: {bg_main};
}}
QTabBar::tab {{
    background-color: {bg_section};
    color: {text_secondary};
    border: 1px solid {border};
    border-bottom-color: transparent;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 5px 12px;
}}
QTabBar::tab:selected, QTabBar::tab:hover {{
    background-color: {bg_main};
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
    border-color: {accent_pressed};
    image: url(check.png); /* Fallback to solid background color if image not found */
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
    background-color: {bg_section};
    color: {text};
    selection-background-color: {accent_muted};
    border: 1px solid {border};
}}
""".format(
    bg_main=BACKGROUND_MAIN,
    bg_section=BACKGROUND_SECTION,
    bg_input=BACKGROUND_INPUT,
    bg_hover=BACKGROUND_HOVER,
    bg_pressed=BACKGROUND_PRESSED,
    accent=ACCENT,
    accent_hover=ACCENT_HOVER,
    accent_pressed=ACCENT_PRESSED,
    accent_muted=ACCENT_MUTED,
    text=TEXT_PRIMARY,
    text_secondary=TEXT_SECONDARY,
    text_disabled=TEXT_DISABLED,
    border=BORDER,
    border_light=BORDER_LIGHT,
    separator=SEPARATOR,
)
