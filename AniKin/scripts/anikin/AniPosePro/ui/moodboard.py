"""
moodboard.py — Pose Mood Board (F-NEW-08).

A free-arrange QGraphicsScene canvas where animators can drop
pose cards and reference images for visual blocking planning.
"""

from anikin.core.qt_compat import QtWidgets, QtCore, QtGui
import json
import maya.cmds as cmds

_DATA_NODE = "anikin_data"
_MOODBOARD_ATTR = "moodboard_layout"


class MoodBoardView(QtWidgets.QGraphicsView):
    """
    The main view for the Mood Board.
    Replaces Zone B's scroll area when toggled.
    """
    def __init__(self, parent=None):
        super(MoodBoardView, self).__init__(parent)
        self.setScene(QtWidgets.QGraphicsScene(self))
        self.scene().setSceneRect(0, 0, 2000, 2000)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        self.setStyleSheet("background-color: #1a1e26; border: none;")
        self.setAcceptDrops(True)
        
        # Add background grid
        self._draw_grid()

    def _draw_grid(self):
        # Draw a faint grid
        pen = QtGui.QPen(QtGui.QColor("#2a2e36"))
        for x in range(0, 2000, 100):
            self.scene().addLine(x, 0, x, 2000, pen)
        for y in range(0, 2000, 100):
            self.scene().addLine(0, y, 2000, y, pen)

    def add_widget_card(self, widget, pos=None):
        """Wraps a PoseCard/ClipCard in a proxy and adds to scene."""
        proxy = QtWidgets.QGraphicsProxyWidget()
        proxy.setWidget(widget)
        proxy.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        proxy.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        
        self.scene().addItem(proxy)
        if pos:
            proxy.setPos(pos)
        else:
            # Default center of current view
            rect = self.mapToScene(self.viewport().rect()).boundingRect()
            proxy.setPos(rect.center() - QtCore.QPointF(widget.width()/2, widget.height()/2))
            
        return proxy

    def add_text_note(self, text, pos=None):
        item = QtWidgets.QGraphicsTextItem(text)
        item.setDefaultTextColor(QtGui.QColor("#ccc"))
        item.setFont(QtGui.QFont("Segoe UI", 12))
        item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        item.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        item.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)
        
        self.scene().addItem(item)
        if pos: item.setPos(pos)
        return item

    # ── Drag and Drop ────────────────────────────────────────────────────────
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
            
    def dragMoveEvent(self, event):
        event.acceptProposedAction()
        
    def dropEvent(self, event):
        pos = self.mapToScene(event.pos())
        if event.mimeData().hasUrls():
            # Image drop
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    self._add_image(path, pos)
                    pos += QtCore.QPointF(20, 20)
        elif event.mimeData().hasText():
            # Text note
            text = event.mimeData().text()
            self.add_text_note(text, pos)
            
        event.acceptProposedAction()
        self.save_layout()

    def _add_image(self, path, pos):
        pix = QtGui.QPixmap(path)
        if pix.isNull(): return
        
        # Scale if too big
        if pix.width() > 300 or pix.height() > 300:
            pix = pix.scaled(300, 300, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            
        item = QtWidgets.QGraphicsPixmapItem(pix)
        item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        item.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        item.setData(0, path) # Store path for serialization
        
        self.scene().addItem(item)
        item.setPos(pos)

    # ── Serialization ────────────────────────────────────────────────────────
    
    def save_layout(self):
        if not cmds.objExists(_DATA_NODE):
            cmds.createNode("transform", name=_DATA_NODE)
            cmds.setAttr(f"{_DATA_NODE}.hiddenInOutliner", True)
            
        if not cmds.attributeQuery(_MOODBOARD_ATTR, node=_DATA_NODE, exists=True):
            cmds.addAttr(_DATA_NODE, longName=_MOODBOARD_ATTR, dataType="string")
            
        layout_data = []
        for item in self.scene().items():
            # We don't save grid lines
            if isinstance(item, QtWidgets.QGraphicsLineItem): continue
            
            entry = {
                "x": item.pos().x(),
                "y": item.pos().y(),
                "z": item.zValue()
            }
            
            if isinstance(item, QtWidgets.QGraphicsPixmapItem):
                entry["type"] = "image"
                entry["path"] = item.data(0)
            elif isinstance(item, QtWidgets.QGraphicsTextItem):
                entry["type"] = "text"
                entry["text"] = item.toPlainText()
            elif isinstance(item, QtWidgets.QGraphicsProxyWidget):
                # We would need a way to ID the widget. For now just save path if we can.
                w = item.widget()
                if hasattr(w, "_entry"):
                    entry["type"] = "card"
                    entry["path"] = w._entry.get("path")
                else:
                    continue
            else:
                continue
                
            layout_data.append(entry)
            
        cmds.setAttr(f"{_DATA_NODE}.{_MOODBOARD_ATTR}", json.dumps(layout_data), type="string")

    def load_layout(self, library):
        self.scene().clear()
        self._draw_grid()
        
        if not cmds.objExists(f"{_DATA_NODE}.{_MOODBOARD_ATTR}"):
            return
            
        try:
            data = json.loads(cmds.getAttr(f"{_DATA_NODE}.{_MOODBOARD_ATTR}") or "[]")
        except Exception:
            return
            
        for entry in data:
            pos = QtCore.QPointF(entry.get("x", 0), entry.get("y", 0))
            z = entry.get("z", 0)
            
            if entry["type"] == "image":
                self._add_image(entry["path"], pos)
                
            elif entry["type"] == "text":
                self.add_text_note(entry["text"], pos)
                
            elif entry["type"] == "card":
                # Need to recreate the card widget
                path = entry["path"]
                # Rough search in library
                poses = library.list_poses()
                clips = library.list_clips()
                found = next((p for p in poses if p["path"] == path), None)
                if found:
                    from anikin.AniPosePro.ui.pose_card import PoseCard
                    card = PoseCard(found)
                    proxy = self.add_widget_card(card, pos)
                    proxy.setZValue(z)
                else:
                    found = next((c for c in clips if c["path"] == path), None)
                    if found:
                        from anikin.AniPosePro.ui.clip_card import ClipCard
                        card = ClipCard(found)
                        proxy = self.add_widget_card(card, pos)
                        proxy.setZValue(z)
