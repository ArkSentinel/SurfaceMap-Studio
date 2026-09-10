"""
PBR Material Customization Settings Panel
Collapsible control sections for real-time adjustments of Normal, Height, Roughness, Metallic, and AO.
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QCheckBox, QScrollArea, QFrame, QPushButton, QFileDialog, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from ..core.pbr_engine import PBRMapSettings
from ..core.presets import PresetManager, DEFAULT_PRESETS
from .widgets import LabeledSlider, CollapsibleSection


class SettingsPanel(QWidget):
    """Control panel allowing real-time customization of all PBR parameters."""
    settingsChanged = pyqtSignal()
    presetChanged = pyqtSignal(str)

    def __init__(self, settings: PBRMapSettings, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.settings = settings
        self._block_signals = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Scroll Area for all settings cards
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        container = QWidget()
        self.content_layout = QVBoxLayout(container)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(10)

        self._build_preset_section()
        self._build_normal_section()
        self._build_height_section()
        self._build_roughness_section()
        self._build_metallic_section()
        self._build_ao_section()
        self._build_specular_orm_section()

        self.content_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

    def _emit_change(self):
        if not self._block_signals:
            self.settingsChanged.emit()

    def _build_preset_section(self):
        box = CollapsibleSection("Material Presets (Ajustes Rápidos)", self)
        
        row1 = QHBoxLayout()
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(PresetManager.get_preset_names())
        self.preset_combo.currentIndexChanged.connect(self._on_preset_selected)
        row1.addWidget(self.preset_combo)
        box.addLayout(row1)

        row2 = QHBoxLayout()
        self.btn_save_preset = QPushButton("Guardar Preset")
        self.btn_save_preset.clicked.connect(self._on_save_preset)
        self.btn_load_preset = QPushButton("Cargar Preset")
        self.btn_load_preset.clicked.connect(self._on_load_preset)
        row2.addWidget(self.btn_save_preset)
        row2.addWidget(self.btn_load_preset)
        box.addLayout(row2)

        self.content_layout.addWidget(box)

    def _build_normal_section(self):
        box = CollapsibleSection("Normal Map Settings", self)

        self.normal_strength = LabeledSlider("Fuerza / Relieve (Strength)", 0.1, 10.0, self.settings.normal_strength, 2, 0.1)
        self.normal_strength.valueChanged.connect(self._on_normal_strength)
        box.addWidget(self.normal_strength)

        self.normal_detail = LabeledSlider("Detalle Fino (High-Pass Detail)", 0.0, 1.5, self.settings.normal_detail, 2, 0.05)
        self.normal_detail.valueChanged.connect(self._on_normal_detail)
        box.addWidget(self.normal_detail)

        self.normal_blur = LabeledSlider("Suavizado Normal (Blur)", 0.0, 5.0, self.settings.normal_blur, 1, 0.2)
        self.normal_blur.valueChanged.connect(self._on_normal_blur)
        box.addWidget(self.normal_blur)

        # Filter algorithm combo
        row_filter = QHBoxLayout()
        lbl_filter = QLabel("Algoritmo de Filtro:")
        lbl_filter.setStyleSheet("color: #909296;")
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Scharr (Alta precisión)", "Sobel (Estándar)", "Simple (Suave)"])
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        row_filter.addWidget(lbl_filter)
        row_filter.addWidget(self.filter_combo)
        box.addLayout(row_filter)

        # Flip Toggles (DirectX / OpenGL format)
        row_flips = QHBoxLayout()
        self.chk_flip_y = QCheckBox("Invertir Verde / Y (DirectX / UE)")
        self.chk_flip_y.setToolTip("Activar para formato normal DirectX (Unreal Engine). Desactivar para OpenGL (Blender / Maya / Unity).")
        self.chk_flip_y.setChecked(self.settings.normal_flip_y)
        self.chk_flip_y.toggled.connect(self._on_flip_y)
        
        self.chk_flip_x = QCheckBox("Invertir Rojo / X")
        self.chk_flip_x.setChecked(self.settings.normal_flip_x)
        self.chk_flip_x.toggled.connect(self._on_flip_x)

        row_flips.addWidget(self.chk_flip_y)
        row_flips.addWidget(self.chk_flip_x)
        box.addLayout(row_flips)

        self.content_layout.addWidget(box)

    def _build_height_section(self):
        box = CollapsibleSection("Height / Displacement Settings", self)

        self.height_contrast = LabeledSlider("Contraste", 0.1, 3.0, self.settings.height_contrast, 2, 0.05)
        self.height_contrast.valueChanged.connect(self._on_height_contrast)
        box.addWidget(self.height_contrast)

        self.height_brightness = LabeledSlider("Brillo / Desplazamiento", -1.0, 1.0, self.settings.height_brightness, 2, 0.05)
        self.height_brightness.valueChanged.connect(self._on_height_brightness)
        box.addWidget(self.height_brightness)

        self.height_blur = LabeledSlider("Suavizado / Reducción de Ruido", 0.0, 10.0, self.settings.height_blur, 1, 0.2)
        self.height_blur.valueChanged.connect(self._on_height_blur)
        box.addWidget(self.height_blur)

        row_src = QHBoxLayout()
        lbl_src = QLabel("Fuente de Altura:")
        lbl_src.setStyleSheet("color: #909296;")
        self.src_combo = QComboBox()
        self.src_combo.addItems([
            "Luminancia Perceptual (Recomendado)",
            "Canal Rojo", "Canal Verde", "Canal Azul", "Max RGB", "Min RGB"
        ])
        self.src_combo.currentIndexChanged.connect(self._on_height_src_changed)
        row_src.addWidget(lbl_src)
        row_src.addWidget(self.src_combo)
        box.addLayout(row_src)

        self.chk_height_invert = QCheckBox("Invertir Altura (Blanco ↔ Negro)")
        self.chk_height_invert.setChecked(self.settings.height_invert)
        self.chk_height_invert.toggled.connect(self._on_height_invert)
        box.addWidget(self.chk_height_invert)

        self.content_layout.addWidget(box)

    def _build_roughness_section(self):
        box = CollapsibleSection("Roughness / Smoothness Settings", self)

        self.rough_base = LabeledSlider("Rugosidad Base (Base Level)", 0.0, 1.0, self.settings.roughness_base, 2, 0.02)
        self.rough_base.valueChanged.connect(self._on_rough_base)
        box.addWidget(self.rough_base)

        self.rough_contrast = LabeledSlider("Contraste de Rugosidad", 0.1, 3.0, self.settings.roughness_contrast, 2, 0.05)
        self.rough_contrast.valueChanged.connect(self._on_rough_contrast)
        box.addWidget(self.rough_contrast)

        self.rough_high_freq = LabeledSlider("Micro-relieve / Frecuencia Alta", 0.0, 1.0, self.settings.roughness_high_freq, 2, 0.05)
        self.rough_high_freq.valueChanged.connect(self._on_rough_hf)
        box.addWidget(self.rough_high_freq)

        self.rough_min = LabeledSlider("Mínima Rugosidad (Clamp Min)", 0.0, 1.0, self.settings.roughness_min, 2, 0.02)
        self.rough_min.valueChanged.connect(self._on_rough_min)
        box.addWidget(self.rough_min)

        self.rough_max = LabeledSlider("Máxima Rugosidad (Clamp Max)", 0.0, 1.0, self.settings.roughness_max, 2, 0.02)
        self.rough_max.valueChanged.connect(self._on_rough_max)
        box.addWidget(self.rough_max)

        self.chk_rough_invert = QCheckBox("Invertir a Suavidad / Glossiness (Unity / Source)")
        self.chk_rough_invert.setChecked(self.settings.roughness_invert)
        self.chk_rough_invert.toggled.connect(self._on_rough_invert)
        box.addWidget(self.chk_rough_invert)

        self.content_layout.addWidget(box)

    def _build_metallic_section(self):
        box = CollapsibleSection("Metallic Settings", self)

        row_mode = QHBoxLayout()
        lbl_mode = QLabel("Modo Metálico:")
        lbl_mode.setStyleSheet("color: #909296;")
        self.metal_mode_combo = QComboBox()
        self.metal_mode_combo.addItems(["Automático (Detección)", "Constante Manual", "Umbral / Máscara"])
        self.metal_mode_combo.currentIndexChanged.connect(self._on_metal_mode_changed)
        row_mode.addWidget(lbl_mode)
        row_mode.addWidget(self.metal_mode_combo)
        box.addLayout(row_mode)

        self.metal_base = LabeledSlider("Valor Metálico Constante", 0.0, 1.0, self.settings.metallic_base_val, 2, 0.05)
        self.metal_base.valueChanged.connect(self._on_metal_base)
        box.addWidget(self.metal_base)

        self.metal_thresh = LabeledSlider("Umbral de Metalicidad", 0.0, 1.0, self.settings.metallic_threshold, 2, 0.02)
        self.metal_thresh.valueChanged.connect(self._on_metal_thresh)
        box.addWidget(self.metal_thresh)

        self.metal_tol = LabeledSlider("Tolerancia / Suavizado Umbral", 0.01, 0.5, self.settings.metallic_tolerance, 2, 0.02)
        self.metal_tol.valueChanged.connect(self._on_metal_tol)
        box.addWidget(self.metal_tol)

        self.chk_metal_invert = QCheckBox("Invertir Metálico")
        self.chk_metal_invert.setChecked(self.settings.metallic_invert)
        self.chk_metal_invert.toggled.connect(self._on_metal_invert)
        box.addWidget(self.chk_metal_invert)

        self.content_layout.addWidget(box)

    def _build_ao_section(self):
        box = CollapsibleSection("Ambient Occlusion (AO) / Cavidad", self)

        self.ao_intensity = LabeledSlider("Intensidad de Oclusión", 0.1, 4.0, self.settings.ao_intensity, 2, 0.1)
        self.ao_intensity.valueChanged.connect(self._on_ao_intensity)
        box.addWidget(self.ao_intensity)

        self.ao_radius = LabeledSlider("Radio de Crevice (Píxeles)", 1, 30, float(self.settings.ao_radius), 0, 1.0)
        self.ao_radius.valueChanged.connect(self._on_ao_radius)
        box.addWidget(self.ao_radius)

        self.ao_contrast = LabeledSlider("Contraste de Sombras AO", 0.5, 3.0, self.settings.ao_contrast, 2, 0.05)
        self.ao_contrast.valueChanged.connect(self._on_ao_contrast)
        box.addWidget(self.ao_contrast)

        self.chk_ao_invert = QCheckBox("Invertir AO")
        self.chk_ao_invert.setChecked(self.settings.ao_invert)
        self.chk_ao_invert.toggled.connect(self._on_ao_invert)
        box.addWidget(self.chk_ao_invert)

        self.content_layout.addWidget(box)

    def _build_specular_orm_section(self):
        box = CollapsibleSection("Specular & ORM Packing", self)

        self.spec_f0 = LabeledSlider("Reflectancia Dieléctrica F0", 0.0, 0.1, self.settings.specular_dielectric_f0, 3, 0.005)
        self.spec_f0.valueChanged.connect(self._on_spec_f0)
        box.addWidget(self.spec_f0)

        orm_info = QLabel("Empaquetado ORM (Unreal / Godot / glTF):\n• Rojo = Ambient Occlusion (AO)\n• Verde = Roughness\n• Azul = Metallic")
        orm_info.setStyleSheet("color: #909296; font-size: 11px; background: #141517; padding: 6px; border-radius: 4px;")
        box.addWidget(orm_info)

        self.content_layout.addWidget(box)

    # Signal handlers
    def _on_preset_selected(self, idx: int):
        name = self.preset_combo.currentText()
        if PresetManager.apply_preset(self.settings, name):
            self.sync_ui_from_settings()
            self.presetChanged.emit(name)
            self._emit_change()

    def _on_save_preset(self):
        path, _ = QFileDialog.getSaveFileName(self, "Guardar Preset de Material", "", "JSON (*.json)")
        if path:
            PresetManager.save_custom_preset(self.settings, path)
            QMessageBox.information(self, "Preset Guardado", f"Preset guardado con éxito en:\n{path}")

    def _on_load_preset(self):
        path, _ = QFileDialog.getOpenFileName(self, "Cargar Preset de Material", "", "JSON (*.json)")
        if path:
            if PresetManager.load_custom_preset(self.settings, path):
                self.sync_ui_from_settings()
                self._emit_change()
                QMessageBox.information(self, "Preset Cargado", "Preset cargado con éxito.")
            else:
                QMessageBox.warning(self, "Error", "No se pudo cargar el archivo de preset seleccionado.")

    def _on_normal_strength(self, val: float):
        self.settings.normal_strength = val
        self._emit_change()

    def _on_normal_detail(self, val: float):
        self.settings.normal_detail = val
        self._emit_change()

    def _on_normal_blur(self, val: float):
        self.settings.normal_blur = val
        self._emit_change()

    def _on_filter_changed(self, idx: int):
        filters = ["scharr", "sobel", "simple"]
        self.settings.normal_filter = filters[idx]
        self._emit_change()

    def _on_flip_y(self, checked: bool):
        self.settings.normal_flip_y = checked
        self._emit_change()

    def _on_flip_x(self, checked: bool):
        self.settings.normal_flip_x = checked
        self._emit_change()

    def _on_height_contrast(self, val: float):
        self.settings.height_contrast = val
        self._emit_change()

    def _on_height_brightness(self, val: float):
        self.settings.height_brightness = val
        self._emit_change()

    def _on_height_blur(self, val: float):
        self.settings.height_blur = val
        self._emit_change()

    def _on_height_src_changed(self, idx: int):
        srcs = ["luminance", "red", "green", "blue", "max_rgb", "min_rgb"]
        self.settings.height_source = srcs[idx]
        self._emit_change()

    def _on_height_invert(self, checked: bool):
        self.settings.height_invert = checked
        self._emit_change()

    def _on_rough_base(self, val: float):
        self.settings.roughness_base = val
        self._emit_change()

    def _on_rough_contrast(self, val: float):
        self.settings.roughness_contrast = val
        self._emit_change()

    def _on_rough_hf(self, val: float):
        self.settings.roughness_high_freq = val
        self._emit_change()

    def _on_rough_min(self, val: float):
        self.settings.roughness_min = val
        self._emit_change()

    def _on_rough_max(self, val: float):
        self.settings.roughness_max = val
        self._emit_change()

    def _on_rough_invert(self, checked: bool):
        self.settings.roughness_invert = checked
        self._emit_change()

    def _on_metal_mode_changed(self, idx: int):
        modes = ["auto", "manual_constant", "threshold"]
        self.settings.metallic_mode = modes[idx]
        self._emit_change()

    def _on_metal_base(self, val: float):
        self.settings.metallic_base_val = val
        self._emit_change()

    def _on_metal_thresh(self, val: float):
        self.settings.metallic_threshold = val
        self._emit_change()

    def _on_metal_tol(self, val: float):
        self.settings.metallic_tolerance = val
        self._emit_change()

    def _on_metal_invert(self, checked: bool):
        self.settings.metallic_invert = checked
        self._emit_change()

    def _on_ao_intensity(self, val: float):
        self.settings.ao_intensity = val
        self._emit_change()

    def _on_ao_radius(self, val: float):
        self.settings.ao_radius = int(val)
        self._emit_change()

    def _on_ao_contrast(self, val: float):
        self.settings.ao_contrast = val
        self._emit_change()

    def _on_ao_invert(self, checked: bool):
        self.settings.ao_invert = checked
        self._emit_change()

    def _on_spec_f0(self, val: float):
        self.settings.specular_dielectric_f0 = val
        self._emit_change()

    def sync_ui_from_settings(self):
        """Updates all UI sliders and inputs to match the current settings object."""
        self._block_signals = True
        
        self.normal_strength.setValue(self.settings.normal_strength)
        self.normal_detail.setValue(self.settings.normal_detail)
        self.normal_blur.setValue(self.settings.normal_blur)
        filter_map = {"scharr": 0, "sobel": 1, "simple": 2}
        self.filter_combo.setCurrentIndex(filter_map.get(self.settings.normal_filter, 0))
        self.chk_flip_y.setChecked(self.settings.normal_flip_y)
        self.chk_flip_x.setChecked(self.settings.normal_flip_x)

        self.height_contrast.setValue(self.settings.height_contrast)
        self.height_brightness.setValue(self.settings.height_brightness)
        self.height_blur.setValue(self.settings.height_blur)
        src_map = {"luminance": 0, "red": 1, "green": 2, "blue": 3, "max_rgb": 4, "min_rgb": 5}
        self.src_combo.setCurrentIndex(src_map.get(self.settings.height_source, 0))
        self.chk_height_invert.setChecked(self.settings.height_invert)

        self.rough_base.setValue(self.settings.roughness_base)
        self.rough_contrast.setValue(self.settings.roughness_contrast)
        self.rough_high_freq.setValue(self.settings.roughness_high_freq)
        self.rough_min.setValue(self.settings.roughness_min)
        self.rough_max.setValue(self.settings.roughness_max)
        self.chk_rough_invert.setChecked(self.settings.roughness_invert)

        mode_map = {"auto": 0, "manual_constant": 1, "threshold": 2}
        self.metal_mode_combo.setCurrentIndex(mode_map.get(self.settings.metallic_mode, 0))
        self.metal_base.setValue(self.settings.metallic_base_val)
        self.metal_thresh.setValue(self.settings.metallic_threshold)
        self.metal_tol.setValue(self.settings.metallic_tolerance)
        self.chk_metal_invert.setChecked(self.settings.metallic_invert)

        self.ao_intensity.setValue(self.settings.ao_intensity)
        self.ao_radius.setValue(float(self.settings.ao_radius))
        self.ao_contrast.setValue(self.settings.ao_contrast)
        self.chk_ao_invert.setChecked(self.settings.ao_invert)

        self.spec_f0.setValue(self.settings.specular_dielectric_f0)

        self._block_signals = False
