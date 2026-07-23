"""
styles.py — QSS Styling & Design Tokens for AniPose Pro V3.3.
Based on AniposeProv3.3UIUX.md PRD tokens.
"""

ANIPOSE_STYLE_QSS = """
QWidget {
    background-color: #2E2E2E; /* surface-0 */
    color: #E8E8E8; /* text-primary */
    font-family: 'Segoe UI', '.SF NS Text', 'San Francisco', sans-serif;
    font-size: 11px;
}

/* Tab widget and pane */
QTabWidget::pane {
    border: 1px solid #1F1F1F; /* border-hairline */
    background: #2E2E2E; /* surface-0 */
}

QTabBar::tab {
    background: #383838; /* surface-1 */
    color: #9A9A9A; /* text-secondary */
    padding: 6px 14px;
    border: 1px solid #1F1F1F; /* border-hairline */
    border-bottom: none;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    font-size: 12px;
    font-weight: 600; /* Semibold */
}

QTabBar::tab:selected {
    background: #454545; /* surface-2 */
    color: #E8E8E8; /* text-primary */
    border-top: 2px solid #2FD3C2; /* accent-motion */
}

QTabBar::tab:hover {
    background: #525252; /* surface-3 */
    color: #E8E8E8;
}

/* Inputs */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #454545; /* surface-2 */
    border: 1px solid #1F1F1F; /* border-hairline */
    border-radius: 4px;
    padding: 4px 8px;
    color: #E8E8E8;
}

QLineEdit:focus, QComboBox:focus {
    border: 1px solid #2FD3C2; /* accent-motion */
}

/* Buttons */
QPushButton {
    background-color: #454545; /* surface-2 (secondary button) */
    border: 1px solid #1F1F1F; /* border-hairline */
    border-radius: 4px;
    padding: 6px 14px;
    color: #E8E8E8;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #525252; /* surface-3 */
}

QPushButton:pressed {
    background-color: #383838; /* surface-1 */
}

/* Primary Button */
QPushButton#primary {
    background-color: #2FD3C2; /* accent-motion */
    color: #1A1A1A;
    font-weight: bold;
    border: none;
}

QPushButton#primary:hover {
    background-color: #1B7A70; /* accent-motion-dim */
}

QPushButton#primary:pressed {
    background-color: #1B7A70;
}

/* Capture / Armed Button */
QPushButton#armed {
    background-color: #E8543F; /* accent-capture */
    color: #1A1A1A;
    font-weight: bold;
    border: none;
}

QPushButton#armed:hover {
    background-color: #D9483D; /* error variant for press */
}

/* Trees and Lists */
QTreeWidget, QListWidget, QTableWidget {
    background-color: #2E2E2E; /* surface-0 */
    border: 1px solid #1F1F1F; /* border-hairline */
    color: #E8E8E8;
}

QTreeWidget::item:selected, QListWidget::item:selected {
    background-color: #1B7A70; /* accent-motion-dim */
    color: #E8E8E8;
}

QTreeWidget::item:hover, QListWidget::item:hover {
    background-color: #525252; /* surface-3 */
}

/* Sliders */
QSlider::groove:horizontal {
    border: 1px solid #1F1F1F;
    height: 6px;
    background: #383838;
    margin: 2px 0;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #2FD3C2;
    border: 1px solid #1B7A70;
    width: 14px;
    height: 14px;
    margin: -4px 0;
    border-radius: 7px;
}

/* GroupBox */
QGroupBox {
    border: 1px solid #1F1F1F;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 8px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 4px;
    color: #9A9A9A;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #2E2E2E;
    width: 10px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:vertical {
    background: #454545;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}
"""
