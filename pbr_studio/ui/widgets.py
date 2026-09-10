"""
Reusable UI Widgets for PBR Studio
Includes custom labeled sliders, collapsible sections, and drag-and-drop targets.
"""

from typing import Callable, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, 
    QDoubleSpinBox, QSpinBox, QToolButton, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QPainter, QColor, QPen, QFont


class LabeledSlider(QWidget):
    """
    A custom slider widget with a title, real-time value display (spinbox),
    min/max bounds, step size, and value changed signal.
    """
    valueChanged = pyqtSignal(float)

    def __init__(
        self, 
        title: str, 
        min_val: float, 
        max_val: float, 
        default_val: float, 
        decimals: int = 2, 
        step: float = 0.05,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.min_val = min_val
        self.max_val = max_val
        self.decimals = decimals
        self.scale_factor = 10 ** decimals
        self._updating = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(4)

        # Header row: Label + SpinBox
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.label = QLabel(title)
        self.label.setStyleSheet("color: #c1c2c5; font-weight: 500;")
        header_layout.addWidget(self.label)
        
        header_layout.addStretch()

        self.spinbox = QDoubleSpinBox() if decimals > 0 else QSpinBox()
        self.spinbox.setRange(min_val, max_val)
        if decimals > 0:
            self.spinbox.setDecimals(decimals)
            self.spinbox.setSingleStep(step)
        else:
            self.spinbox.setSingleStep(int(step) if step >= 1 else 1)
        self.spinbox.setValue(default_val)
        self.spinbox.setFixedWidth(68)
        self.spinbox.setStyleSheet("background-color: #202124; border: 1px solid #373a40; border-radius: 4px; padding: 2px 4px;")
        header_layout.addWidget(self.spinbox)

        layout.addLayout(header_layout)

        # Slider row
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(int(min_val * self.scale_factor), int(max_val * self.scale_factor))
        self.slider.setValue(int(default_val * self.scale_factor))
        layout.addWidget(self.slider)

        # Connect signals
        self.slider.valueChanged.connect(self._on_slider_changed)
        self.spinbox.valueChanged.connect(self._on_spinbox_changed)

    def _on_slider_changed(self, value: int):
        if self._updating:
            return
        self._updating = True
        float_val = value / self.scale_factor
        self.spinbox.setValue(float_val)
        self._updating = False
        self.valueChanged.emit(float_val)

    def _on_spinbox_changed(self, value: float):
        if self._updating:
            return
        self._updating = True
        self.slider.setValue(int(value * self.scale_factor))
        self._updating = False
        self.valueChanged.emit(float(value))

    def value(self) -> float:
        return float(self.spinbox.value())

    def setValue(self, val: float):
        self._updating = True
        self.spinbox.setValue(val)
        self.slider.setValue(int(val * self.scale_factor))
        self._updating = False


class CollapsibleSection(QWidget):
    """
    A collapsible settings section with a modern toggle header.
    """
    def __init__(self, title: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.is_collapsed = False

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 2, 0, 6)
        self.main_layout.setSpacing(0)

        # Header button
        self.toggle_btn = QToolButton(self)
        self.toggle_btn.setStyleSheet(
            "QToolButton { border: none; font-weight: bold; color: #60a5fa; "
            "background-color: #202124; border-radius: 6px; padding: 6px 10px; text-align: left; }"
            "QToolButton:hover { background-color: #2c2e33; }"
        )
        self.toggle_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toggle_btn.setArrowType(Qt.ArrowType.DownArrow)
        self.toggle_btn.setText(f"  {title}")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(True)
        self.toggle_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.toggle_btn.clicked.connect(self._on_toggle)
        self.main_layout.addWidget(self.toggle_btn)

        # Content frame
        self.content_area = QFrame(self)
        self.content_area.setStyleSheet(
            "QFrame { background-color: #18191c; border: 1px solid #27292e; border-top: none; "
            "border-bottom-left-radius: 6px; border-bottom-right-radius: 6px; padding: 8px; }"
        )
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(8)
        self.main_layout.addWidget(self.content_area)

    def _on_toggle(self):
        checked = self.toggle_btn.isChecked()
        self.toggle_btn.setArrowType(Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow)
        self.content_area.setVisible(checked)

    def addWidget(self, widget: QWidget):
        self.content_layout.addWidget(widget)

    def addLayout(self, layout):
        self.content_layout.addLayout(layout)


class DropZoneWidget(QFrame):
    """
    A drag-and-drop file target area.
    """
    fileDropped = pyqtSignal(str)
    filesDropped = pyqtSignal(list)
    clicked = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.is_drag_active = False
        self.setMinimumHeight(120)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and any(u.isLocalFile() for u in urls):
                self.is_drag_active = True
                self.update()
                event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self.is_drag_active = False
        self.update()

    def dropEvent(self, event: QDropEvent):
        self.is_drag_active = False
        urls = event.mimeData().urls()
        local_files = [u.toLocalFile() for u in urls if u.isLocalFile()]
        if local_files:
            self.fileDropped.emit(local_files[0])
            self.filesDropped.emit(local_files)
            event.acceptProposedAction()
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(2, 2, -2, -2)
        bg_color = QColor("#22252a") if self.is_drag_active else QColor("#1a1b1e")
        border_color = QColor("#3b82f6") if self.is_drag_active else QColor("#373a40")

        painter.setBrush(bg_color)
        pen = QPen(border_color, 2, Qt.PenStyle.DashLine if not self.is_drag_active else Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        painter.drawRoundedRect(rect, 8, 8)

        # Draw text
        painter.setPen(QColor("#909296"))
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        painter.setFont(font)
        
        text1 = "Arrastra y suelta tus texturas aqui" if not self.is_drag_active else "Soltar imagenes aqui"
        text2 = "(o haz clic para seleccionar una o varias imagenes - PNG, JPG, TGA, TIFF, WEBP)"
        
        font_sub = QFont()
        font_sub.setPointSize(10)

        painter.drawText(rect.adjusted(0, -12, 0, 0), Qt.AlignmentFlag.AlignCenter, text1)
        painter.setFont(font_sub)
        painter.setPen(QColor("#5c5f66"))
        painter.drawText(rect.adjusted(0, 24, 0, 0), Qt.AlignmentFlag.AlignCenter, text2)
