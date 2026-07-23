"""
styles.py — QSS Styling & Design Tokens for AniPose Pro V3.1.
Design tokens:
- Window background: #0d0f10
- Panel surfaces: #161a1d
- Cards: #1e2428
- Borders: #2a3038
- Text primary: #f0f2f4
- Text secondary: #8b9299
- Accent (ARMED state, primary buttons): #d4860a
- Success (mirror / active badges): #3a9e6e
"""

ANIPOSE_STYLE_QSS = """
QWidget {
    background-color: #0d0f10;
    color: #f0f2f4;
    font-family: 'Segoe UI', Roboto, sans-serif;
    font-size: 12px;
}

QTabWidget::pane {
    border: 1px solid #2a3038;
    background: #161a1d;
}

QTabBar::tab {
    background: #161a1d;
    color: #8b9299;
    padding: 6px 14px;
    border: 1px solid #2a3038;
    border-bottom: none;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background: #1e2428;
    color: #f0f2f4;
    border-top: 2px solid #d4860a;
}

QTabBar::tab:hover {
    background: #252b30;
    color: #f0f2f4;
}

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #161a1d;
    border: 1px solid #2a3038;
    border-radius: 4px;
    padding: 4px 8px;
    color: #f0f2f4;
}

QLineEdit:focus, QComboBox:focus {
    border: 1px solid #d4860a;
}

QPushButton {
    background-color: #1e2428;
    border: 1px solid #2a3038;
    border-radius: 4px;
    padding: 6px 12px;
    color: #f0f2f4;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #2a3038;
    border-color: #404854;
}

QPushButton:pressed {
    background-color: #121518;
}

QPushButton#primary {
    background-color: #d4860a;
    color: #0d0f10;
    font-weight: bold;
    border: none;
}

QPushButton#primary:hover {
    background-color: #e59416;
}

QPushButton#armed {
    background-color: #d4860a;
    color: #0d0f10;
    font-weight: bold;
    border: 2px solid #ffaa00;
}

QTreeWidget, QListWidget, QTableWidget {
    background-color: #161a1d;
    border: 1px solid #2a3038;
    color: #f0f2f4;
}

QTreeWidget::item:selected, QListWidget::item:selected {
    background-color: #2a3038;
    color: #d4860a;
}

QSlider::groove:horizontal {
    border: 1px solid #2a3038;
    height: 6px;
    background: #161a1d;
    margin: 2px 0;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #d4860a;
    border: 1px solid #ffaa00;
    width: 14px;
    height: 14px;
    margin: -4px 0;
    border-radius: 7px;
}

QGroupBox {
    border: 1px solid #2a3038;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 8px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 4px;
    color: #8b9299;
}
"""
