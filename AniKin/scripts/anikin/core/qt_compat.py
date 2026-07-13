"""
qt_compat.py
PySide2 / PySide6 compatibility shim.

Maya 2022–2024 ship PySide2; Maya 2025+ ship PySide6.
This module detects which is available and re-exports a unified namespace
so the rest of AniKin never has to care.
"""

try:
    from PySide6 import QtWidgets, QtCore, QtGui
    from shiboken6 import wrapInstance
    PYSIDE_VERSION = 6
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui
    from shiboken2 import wrapInstance
    PYSIDE_VERSION = 2

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

try:
    MIDDLE_BUTTON = QtCore.Qt.MouseButton.MiddleButton  # PySide6
except AttributeError:
    MIDDLE_BUTTON = QtCore.Qt.MiddleButton              # PySide2

def get_maya_main_window():
    """Return the Maya main window as a QWidget so we can parent dialogs to it."""
    import maya.OpenMayaUI as omui
    main_window_ptr = omui.MQtUtil.mainWindow()
    if main_window_ptr is None:
        return None
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)
