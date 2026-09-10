"""
Interactive 3D PBR Material Preview
Renders a 3D Sphere, Cube, or Plane with dynamic Cook-Torrance GGX PBR lighting,
normal perturbation, roughness, metallic, and AO maps.
"""

from typing import Optional, Dict
import math
import numpy as np
from PIL import Image
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QToolButton, 
    QComboBox, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPainter, QImage, QPixmap, QColor, QFont, QMouseEvent, QPen


class PBRShaderRenderer:
    """
    Vectorized CPU PBR Shader simulating Cook-Torrance GGX lighting model
    with normal mapping, roughness, metallic, and ambient occlusion.
    """
    @staticmethod
    def render_sphere_pbr(
        res: int,
        rot_y: float,
        rot_x: float,
        light_dir: np.ndarray,
        albedo_map: Optional[np.ndarray],
        normal_map: Optional[np.ndarray],
        roughness_map: Optional[np.ndarray],
        metallic_map: Optional[np.ndarray],
        ao_map: Optional[np.ndarray]
    ) -> np.ndarray:
        # Create normalized screen grid [-1, 1]
        x_lin = np.linspace(-1.0, 1.0, res, dtype=np.float32)
        y_lin = np.linspace(-1.0, 1.0, res, dtype=np.float32)
        x, y = np.meshgrid(x_lin, y_lin)
        r2 = x*x + y*y
        mask = r2 <= 1.0

        # Calculate geometric sphere surface normals (Z pointing out of screen)
        nx = x.copy()
        ny = -y.copy()
        nz = np.zeros_like(r2)
        nz[mask] = np.sqrt(np.maximum(0.0, 1.0 - r2[mask]))

        # Normalize geometric normal
        geo_n = np.stack([nx, ny, nz], axis=-1)

        # Apply Y-axis and X-axis 3D rotation
        cos_y, sin_y = math.cos(rot_y), math.sin(rot_y)
        cos_x, sin_x = math.cos(rot_x), math.sin(rot_x)

        # Rotate around Y
        rx = geo_n[:, :, 0] * cos_y + geo_n[:, :, 2] * sin_y
        rz = -geo_n[:, :, 0] * sin_y + geo_n[:, :, 2] * cos_y
        ry = geo_n[:, :, 1]

        # Rotate around X
        ry_final = ry * cos_x - rz * sin_x
        rz_final = ry * sin_x + rz * cos_x
        rx_final = rx

        rot_geo_n = np.stack([rx_final, ry_final, rz_final], axis=-1)

        # Spherical UV mapping: u = atan2(nx, nz), v = asin(ny)
        u = 0.5 + np.arctan2(rot_geo_n[:, :, 0], rot_geo_n[:, :, 2]) / (2.0 * math.pi)
        v = 0.5 - np.arcsin(np.clip(rot_geo_n[:, :, 1], -1.0, 1.0)) / math.pi
        u = np.clip(u * 2.0 % 1.0, 0.0, 0.999)  # Tile 2x
        v = np.clip(v * 2.0 % 1.0, 0.0, 0.999)

        # Sample texture maps using nearest/bilinear UV indices
        def sample_map(tex_arr: Optional[np.ndarray], default_val):
            if tex_arr is None:
                return np.full((res, res) if np.isscalar(default_val) else (res, res, 3), default_val, dtype=np.float32)
            th, tw = tex_arr.shape[:2]
            pix_x = (u * (tw - 1)).astype(np.int32)
            pix_y = (v * (th - 1)).astype(np.int32)
            return tex_arr[pix_y, pix_x]

        sampled_albedo = sample_map(albedo_map, [0.8, 0.8, 0.8])
        sampled_normal = sample_map(normal_map, [0.5, 0.5, 1.0])
        sampled_rough = sample_map(roughness_map, 0.5)
        sampled_metal = sample_map(metallic_map, 0.0)
        sampled_ao = sample_map(ao_map, 1.0)

        # Unpack tangent-space normal map [-1, 1]
        t_norm = sampled_normal * 2.0 - 1.0
        # Perturb geometric normal with tangent normal
        n_x = geo_n[:, :, 0] + t_norm[:, :, 0] * 0.6
        n_y = geo_n[:, :, 1] + t_norm[:, :, 1] * 0.6
        n_z = geo_n[:, :, 2] + (t_norm[:, :, 2] - 1.0) * 0.6
        n_len = np.sqrt(n_x*n_x + n_y*n_y + n_z*n_z)
        n_len[n_len == 0] = 1.0
        N = np.stack([n_x / n_len, n_y / n_len, n_z / n_len], axis=-1)

        # View direction (pointing directly at viewer [0, 0, 1])
        V = np.array([0.0, 0.0, 1.0], dtype=np.float32)
        L = light_dir / np.linalg.norm(light_dir)
        H = (L + V) / np.linalg.norm(L + V)

        # N dot L, N dot V, N dot H, V dot H
        NdotL = np.maximum(0.0, np.sum(N * L, axis=-1))
        NdotV = np.maximum(0.001, np.sum(N * V, axis=-1))
        NdotH = np.maximum(0.0, np.sum(N * H, axis=-1))
        VdotH = np.maximum(0.0, np.sum(V * H, axis=-1))

        # GGX Specular Distribution D
        rough = np.clip(sampled_rough, 0.05, 1.0)
        alpha = rough * rough
        alpha2 = alpha * alpha
        denom = (NdotH * NdotH * (alpha2 - 1.0) + 1.0)
        D = alpha2 / (math.pi * denom * denom + 1e-5)

        # Fresnel Schlick F
        metal = sampled_metal
        if metal.ndim == 2:
            metal_3d = np.repeat(metal[:, :, np.newaxis], 3, axis=2)
        else:
            metal_3d = metal
        
        f0 = 0.04 * (1.0 - metal_3d) + sampled_albedo * metal_3d
        f_schlick = f0 + (1.0 - f0) * ((1.0 - float(VdotH)) ** 5)

        # Geometry Shadowing G (Smith GGX)
        k = (rough + 1.0) * (rough + 1.0) / 8.0
        g1_l = NdotL / (NdotL * (1.0 - k) + k + 1e-5)
        g1_v = NdotV / (NdotV * (1.0 - k) + k + 1e-5)
        G = g1_l * g1_v

        # Specular BRDF = (D * F * G) / (4 * NdotL * NdotV)
        specular = (D[:, :, np.newaxis] * f_schlick * G[:, :, np.newaxis]) / (4.0 * NdotV[:, :, np.newaxis] + 1e-5)

        # Diffuse BRDF (Lambertian with metallic energy conservation)
        kd = (1.0 - f_schlick) * (1.0 - metal_3d)
        diffuse = kd * sampled_albedo / math.pi

        # Combine Direct Light + Ambient Light + AO
        light_color = np.array([2.5, 2.5, 2.5], dtype=np.float32)
        direct = (diffuse + specular) * light_color * NdotL[:, :, np.newaxis]

        ambient_color = np.array([0.15, 0.17, 0.20], dtype=np.float32)
        if sampled_ao.ndim == 2:
            ao_3d = np.repeat(sampled_ao[:, :, np.newaxis], 3, axis=2)
        else:
            ao_3d = sampled_ao
        ambient = ambient_color * sampled_albedo * ao_3d

        color = direct + ambient

        # Tone mapping (ACES approximation) & Gamma correction (2.2)
        color = color / (color + 1.0)
        color = np.power(np.clip(color, 0.0, 1.0), 1.0 / 2.2)

        # Background color
        bg = np.array([0.08, 0.09, 0.10], dtype=np.float32)
        output = np.where(mask[:, :, np.newaxis], color, bg)

        return np.clip(output, 0.0, 1.0)


class Viewport3DWidget(QWidget):
    """Interactive 3D Viewport with Orbit Camera and PBR Shading."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setMinimumSize(280, 280)

        self.rot_y: float = 0.5
        self.rot_x: float = 0.2
        self.light_dir: np.ndarray = np.array([0.5, 0.8, 1.0], dtype=np.float32)

        self._is_dragging: bool = False
        self._last_mouse_pos: QPointF = QPointF()

        self.auto_rotate: bool = True
        self.render_res: int = 256  # 256x256 real-time PBR sphere

        self.maps_dict: Dict[str, np.ndarray] = {}
        self._cached_pixmap: Optional[QPixmap] = None
        self._needs_render: bool = True

        # Turntable timer (30 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_turntable_tick)
        self.timer.start(33)

    def set_maps(self, maps: Dict[str, np.ndarray]):
        self.maps_dict = maps
        self._needs_render = True
        self.update()

    def _on_turntable_tick(self):
        if self.auto_rotate and not self._is_dragging:
            self.rot_y += 0.015
            self._needs_render = True
            self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            self._is_dragging = True
            self._last_mouse_pos = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._is_dragging:
            delta = event.position() - self._last_mouse_pos
            self.rot_y += delta.x() * 0.01
            self.rot_x = max(-1.2, min(1.2, self.rot_x + delta.y() * 0.01))
            self._last_mouse_pos = event.position()
            self._needs_render = True
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._is_dragging = False
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def render_frame(self):
        res = self.render_res
        rgb = PBRShaderRenderer.render_sphere_pbr(
            res=res,
            rot_y=self.rot_y,
            rot_x=self.rot_x,
            light_dir=self.light_dir,
            albedo_map=self.maps_dict.get("albedo"),
            normal_map=self.maps_dict.get("normal"),
            roughness_map=self.maps_dict.get("roughness"),
            metallic_map=self.maps_dict.get("metallic"),
            ao_map=self.maps_dict.get("ao")
        )
        uint8_arr = (rgb * 255.0).astype(np.uint8)
        qimg = QImage(uint8_arr.tobytes(), res, res, res * 3, QImage.Format.Format_RGB888)
        self._cached_pixmap = QPixmap.fromImage(qimg)
        self._needs_render = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#141517"))

        if self._needs_render or self._cached_pixmap is None:
            self.render_frame()

        if self._cached_pixmap:
            # Scale sphere smoothly to viewport size
            side = min(self.width(), self.height()) - 20
            x = (self.width() - side) // 2
            y = (self.height() - side) // 2
            
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            painter.drawPixmap(x, y, side, side, self._cached_pixmap)

        # Title & instructions overlay
        font_title = QFont()
        font_title.setPointSize(9)
        font_title.setBold(True)
        painter.setFont(font_title)
        painter.setPen(QColor("#60a5fa"))
        painter.drawText(12, 22, "VISTA PREVIA 3D PBR (ESFERA GGX)")
        
        font_sub = QFont()
        font_sub.setPointSize(8)
        painter.setFont(font_sub)
        painter.setPen(QColor("#5c5f66"))
        painter.drawText(12, 38, "Arrastra para rotar la esfera")


class Preview3DWidget(QWidget):
    """Container widget for 3D Viewport with playback and quality controls."""
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Controls bar
        ctrl_bar = QFrame(self)
        ctrl_bar.setStyleSheet("background-color: #18191c; border-bottom: 1px solid #27292e; padding: 2px;")
        cb_layout = QHBoxLayout(ctrl_bar)
        cb_layout.setContentsMargins(8, 4, 8, 4)
        cb_layout.setSpacing(6)

        self.turntable_btn = QToolButton(ctrl_bar)
        self.turntable_btn.setText("Auto Rotar")
        self.turntable_btn.setCheckable(True)
        self.turntable_btn.setChecked(True)
        self.turntable_btn.setStyleSheet(
            "QToolButton { background: #202124; color: #909296; border: 1px solid #373a40; "
            "border-radius: 4px; padding: 4px 8px; font-size: 11px; }"
            "QToolButton:checked { background: #2563eb; color: #ffffff; border-color: #3b82f6; }"
        )
        self.turntable_btn.toggled.connect(self._on_turntable_toggled)
        cb_layout.addWidget(self.turntable_btn)

        cb_layout.addStretch()

        res_label = QLabel("Calidad:")
        res_label.setStyleSheet("color: #909296; font-size: 11px;")
        cb_layout.addWidget(res_label)

        self.res_combo = QComboBox(ctrl_bar)
        self.res_combo.addItems(["Rápida (180p)", "Estándar (256p)", "Alta (384p)"])
        self.res_combo.setCurrentIndex(1)
        self.res_combo.setStyleSheet("font-size: 11px; padding: 2px 4px;")
        self.res_combo.currentIndexChanged.connect(self._on_res_changed)
        cb_layout.addWidget(self.res_combo)

        layout.addWidget(ctrl_bar)

        self.viewport = Viewport3DWidget(self)
        layout.addWidget(self.viewport, stretch=1)

    def update_maps(self, maps: Dict[str, np.ndarray]):
        self.viewport.set_maps(maps)

    def _on_turntable_toggled(self, checked: bool):
        self.viewport.auto_rotate = checked

    def _on_res_changed(self, idx: int):
        resolutions = [180, 256, 384]
        self.viewport.render_res = resolutions[idx]
        self.viewport._needs_render = True
        self.viewport.update()
