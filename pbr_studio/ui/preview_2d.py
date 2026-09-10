"""
2D Image Preview Widget
Interactive viewport supporting zoom, pan, 1:1 pixel inspection, and split-screen comparison.
"""

from typing import Optional, Dict
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QToolButton, 
    QButtonGroup, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import QPainter, QPixmap, QImage, QColor, QPen, QWheelEvent, QMouseEvent, QFont
from ..core.pbr_engine import PBREngine


class InteractiveImageViewport(QWidget):
    """
    High-performance custom viewport supporting smooth zoom, pan, and split-screen slider.
    """
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._pixmap_a: Optional[QPixmap] = None  # Original / Reference
        self._pixmap_b: Optional[QPixmap] = None  # Current Selected Map
        
        self._scale: float = 1.0
        self._offset_x: float = 0.0
        self._offset_y: float = 0.0
        
        self._is_panning: bool = False
        self._pan_start: QPointF = QPointF()
        
        # Split screen slider mode
        self.split_mode: bool = False
        self.split_pos_pct: float = 0.5  # 0.0 to 1.0
        self._is_dragging_splitter: bool = False

        self.setStyleSheet("background-color: #121315;")

    def set_images(self, pixmap_b: Optional[QPixmap], pixmap_a: Optional[QPixmap] = None):
        """Sets the active map (B) and optional reference image (A)."""
        self._pixmap_b = pixmap_b
        if pixmap_a is not None:
            self._pixmap_a = pixmap_a
        self.update()

    def reset_view(self):
        """Fits the image nicely into the viewport."""
        if not self._pixmap_b and not self._pixmap_a:
            return
        
        target = self._pixmap_b or self._pixmap_a
        vw, vh = self.width(), self.height()
        iw, ih = target.width(), target.height()

        if iw == 0 or ih == 0 or vw == 0 or vh == 0:
            return

        scale_w = (vw - 40) / iw
        scale_h = (vh - 40) / ih
        self._scale = min(scale_w, scale_h, 1.0)
        if self._scale <= 0:
            self._scale = 1.0

        self._offset_x = (vw - iw * self._scale) / 2.0
        self._offset_y = (vh - ih * self._scale) / 2.0
        self.update()

    def set_actual_size(self):
        """Resets zoom scale to 100% (1:1)."""
        if not self._pixmap_b and not self._pixmap_a:
            return
        target = self._pixmap_b or self._pixmap_a
        self._scale = 1.0
        self._offset_x = (self.width() - target.width()) / 2.0
        self._offset_y = (self.height() - target.height()) / 2.0
        self.update()

    def wheelEvent(self, event: QWheelEvent):
        """Smooth mouse-wheel zoom centered on cursor."""
        if not self._pixmap_b and not self._pixmap_a:
            return

        delta = event.angleDelta().y()
        if delta == 0:
            return

        zoom_factor = 1.15 if delta > 0 else (1.0 / 1.15)
        new_scale = max(0.05, min(self._scale * zoom_factor, 32.0))

        # Center zoom on mouse position
        pos = event.position()
        self._offset_x = pos.x() - (pos.x() - self._offset_x) * (new_scale / self._scale)
        self._offset_y = pos.y() - (pos.y() - self._offset_y) * (new_scale / self._scale)
        self._scale = new_scale
        
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if clicking near split slider
            if self.split_mode:
                split_screen_x = self.width() * self.split_pos_pct
                if abs(event.position().x() - split_screen_x) < 14:
                    self._is_dragging_splitter = True
                    return

            self._is_panning = True
            self._pan_start = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            
        elif event.button() in (Qt.MouseButton.MiddleButton, Qt.MouseButton.RightButton):
            self._is_panning = True
            self._pan_start = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._is_dragging_splitter:
            self.split_pos_pct = max(0.02, min(0.98, event.position().x() / max(1, self.width())))
            self.update()
            return

        if self._is_panning:
            delta = event.position() - self._pan_start
            self._offset_x += delta.x()
            self._offset_y += delta.y()
            self._pan_start = event.position()
            self.update()
            return

        # Cursor hover update for split slider
        if self.split_mode:
            split_screen_x = self.width() * self.split_pos_pct
            if abs(event.position().x() - split_screen_x) < 14:
                self.setCursor(Qt.CursorShape.SplitHCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._is_panning = False
        self._is_dragging_splitter = False
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.fillRect(self.rect(), QColor("#141517"))

        # Draw checkered background for transparency/texture grid
        self._draw_grid_pattern(painter)

        target = self._pixmap_b or self._pixmap_a
        if not target or target.isNull():
            painter.setPen(QColor("#5c5f66"))
            font = QFont()
            font.setPointSize(13)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Sin textura cargada\nArrastra una imagen o selecciónala arriba")
            return

        img_rect = QRectF(self._offset_x, self._offset_y, target.width() * self._scale, target.height() * self._scale)

        if not self.split_mode or not self._pixmap_a or not self._pixmap_b:
            # Standard single map view
            active_pix = self._pixmap_b or self._pixmap_a
            painter.drawPixmap(img_rect.toRect(), active_pix)
        else:
            # Split-screen comparison view
            split_x = int(self.width() * self.split_pos_pct)

            # Draw Left: Original (pixmap_a)
            painter.save()
            painter.setClipRect(0, 0, split_x, self.height())
            painter.drawPixmap(img_rect.toRect(), self._pixmap_a)
            painter.restore()

            # Draw Right: Generated Map (pixmap_b)
            painter.save()
            painter.setClipRect(split_x, 0, self.width() - split_x, self.height())
            painter.drawPixmap(img_rect.toRect(), self._pixmap_b)
            painter.restore()

            # Draw Splitter Line and Handle
            painter.setPen(QPen(QColor("#3b82f6"), 2))
            painter.drawLine(split_x, 0, split_x, self.height())

            handle_rect = QRectF(split_x - 12, self.height() / 2 - 24, 24, 48)
            painter.setBrush(QColor("#2563eb"))
            painter.setPen(QPen(QColor("#ffffff"), 1.5))
            painter.drawRoundedRect(handle_rect, 6, 6)

            # Splitter arrow icons
            painter.setPen(QPen(QColor("#ffffff"), 2))
            mid_y = self.height() / 2
            painter.drawLine(int(split_x - 5), int(mid_y), int(split_x - 2), int(mid_y - 4))
            painter.drawLine(int(split_x - 5), int(mid_y), int(split_x - 2), int(mid_y + 4))
            painter.drawLine(int(split_x + 5), int(mid_y), int(split_x + 2), int(mid_y - 4))
            painter.drawLine(int(split_x + 5), int(mid_y), int(split_x + 2), int(mid_y + 4))

        # Draw Zoom overlay badge in top-right corner
        zoom_text = f"{int(self._scale * 100)}%"
        badge_font = QFont()
        badge_font.setPointSize(10)
        badge_font.setBold(True)
        painter.setFont(badge_font)
        badge_w, badge_h = 56, 24
        badge_rect = QRectF(self.width() - badge_w - 12, 12, badge_w, badge_h)
        painter.setBrush(QColor(20, 21, 23, 200))
        painter.setPen(QPen(QColor("#373a40"), 1))
        painter.drawRoundedRect(badge_rect, 4, 4)
        painter.setPen(QColor("#c1c2c5"))
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, zoom_text)

    def _draw_grid_pattern(self, painter: QPainter):
        """Draw subtle checkerboard background."""
        grid_size = 20
        c1 = QColor("#18191c")
        c2 = QColor("#1e1f23")
        w, h = self.width(), self.height()
        
        for y in range(0, h, grid_size):
            for x in range(0, w, grid_size):
                if ((x // grid_size) + (y // grid_size)) % 2 == 0:
                    painter.fillRect(x, y, grid_size, grid_size, c1)
                else:
                    painter.fillRect(x, y, grid_size, grid_size, c2)


class Preview2DWidget(QWidget):
    """
    Complete 2D Preview interface with map switch tabs/buttons, zoom controls,
    and split comparison toggle.
    """
    mapSelected = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.maps_pixmaps: Dict[str, QPixmap] = {}
        self.current_map_key: str = "normal"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Top Control Bar
        toolbar = QFrame(self)
        toolbar.setStyleSheet("background-color: #18191c; border-bottom: 1px solid #27292e; padding: 4px;")
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(8, 4, 8, 4)
        tb_layout.setSpacing(6)

        # Map Selector Buttons
        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        self.map_buttons = {}
        maps_info = [
            ("albedo", "Albedo / Base"),
            ("normal", "Normal"),
            ("height", "Height"),
            ("roughness", "Roughness"),
            ("metallic", "Metallic"),
            ("ao", "AO"),
            ("specular", "Specular"),
            ("orm", "ORM Packed")
        ]

        for key, label in maps_info:
            btn = QToolButton(toolbar)
            btn.setText(label)
            btn.setCheckable(True)
            btn.setStyleSheet(
                "QToolButton { background: #202124; color: #909296; border: 1px solid #373a40; "
                "border-radius: 4px; padding: 5px 10px; font-weight: 500; font-size: 11px; }"
                "QToolButton:checked { background: #2563eb; color: #ffffff; border-color: #3b82f6; font-weight: bold; }"
                "QToolButton:hover:!checked { background: #2c2e33; color: #e4e5e7; }"
            )
            btn.clicked.connect(lambda checked, k=key: self._on_map_btn_clicked(k))
            self.btn_group.addButton(btn)
            tb_layout.addWidget(btn)
            self.map_buttons[key] = btn

        self.map_buttons["normal"].setChecked(True)

        tb_layout.addStretch()

        # Split comparison button
        self.split_btn = QToolButton(toolbar)
        self.split_btn.setText("Comparar Split")
        self.split_btn.setCheckable(True)
        self.split_btn.setToolTip("Divide la pantalla para comparar la textura original con el mapa generado")
        self.split_btn.setStyleSheet(
            "QToolButton { background: #25262b; color: #60a5fa; border: 1px solid #3b82f6; "
            "border-radius: 4px; padding: 5px 10px; font-weight: 500; font-size: 11px; }"
            "QToolButton:checked { background: #3b82f6; color: #ffffff; }"
        )
        self.split_btn.toggled.connect(self._on_split_toggled)
        tb_layout.addWidget(self.split_btn)

        # Fit & 1:1 Buttons
        self.fit_btn = QToolButton(toolbar)
        self.fit_btn.setText("Ajustar")
        self.fit_btn.setToolTip("Ajustar imagen a la ventana")
        self.fit_btn.clicked.connect(self._on_fit_clicked)
        tb_layout.addWidget(self.fit_btn)

        self.actual_btn = QToolButton(toolbar)
        self.actual_btn.setText("1:1")
        self.actual_btn.setToolTip("Tamaño real 100%")
        self.actual_btn.clicked.connect(self._on_actual_clicked)
        tb_layout.addWidget(self.actual_btn)

        layout.addWidget(toolbar)

        # Main Viewport
        self.viewport = InteractiveImageViewport(self)
        layout.addWidget(self.viewport, stretch=1)

    def update_maps(self, maps_dict: Dict[str, np.ndarray]):
        """Updates all map pixmaps from numpy arrays."""
        self.maps_pixmaps.clear()
        
        for key, arr in maps_dict.items():
            pil_img = PBREngine.numpy_to_image(arr)
            # Convert PIL to QImage
            if pil_img.mode == "L":
                pil_img = pil_img.convert("RGB")
            
            data = pil_img.tobytes("raw", "RGB")
            qimg = QImage(data, pil_img.width, pil_img.height, pil_img.width * 3, QImage.Format.Format_RGB888)
            pix = QPixmap.fromImage(qimg)
            self.maps_pixmaps[key] = pix

        # Set current pixmaps
        active_pix = self.maps_pixmaps.get(self.current_map_key, None)
        orig_pix = self.maps_pixmaps.get("albedo", None)
        self.viewport.set_images(active_pix, orig_pix)

    def select_map(self, map_key: str):
        if map_key in self.map_buttons:
            self.map_buttons[map_key].setChecked(True)
            self._on_map_btn_clicked(map_key)

    def _on_map_btn_clicked(self, map_key: str):
        self.current_map_key = map_key
        active_pix = self.maps_pixmaps.get(map_key, None)
        orig_pix = self.maps_pixmaps.get("albedo", None)
        self.viewport.set_images(active_pix, orig_pix)
        self.mapSelected.emit(map_key)

    def _on_split_toggled(self, checked: bool):
        self.viewport.split_mode = checked
        self.viewport.update()

    def _on_fit_clicked(self):
        self.viewport.reset_view()

    def _on_actual_clicked(self):
        self.viewport.set_actual_size()
