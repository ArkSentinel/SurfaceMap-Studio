"""
PBR Material Export Dialog
Configurable multi-format, multi-resolution batch exporter for generated PBR textures.
"""

import os
from typing import Dict, Optional
import numpy as np
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QCheckBox, QFileDialog, QGroupBox, 
    QGridLayout, QMessageBox, QSpinBox
)
from PyQt6.QtCore import Qt
from ..core.exporter import ExportConfig, PBRExporter


class ExportDialog(QDialog):
    """Dialog for configuring and executing PBR texture export."""
    def __init__(
        self, 
        maps_dict: Dict[str, np.ndarray], 
        default_dir: str = "", 
        default_name: str = "material",
        parent: Optional[QDialog] = None
    ):
        super().__init__(parent)
        self.setWindowTitle("Exportar Material PBR")
        self.setMinimumWidth(520)
        self.setStyleSheet("background-color: #1a1b1e; color: #e4e5e7;")

        self.maps_dict = maps_dict
        self.config = ExportConfig()
        self.config.output_directory = default_dir or os.path.expanduser("~/Desktop")
        self.config.base_name = default_name

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # 1. Output Destination
        dest_group = QGroupBox("Destino y Nombre")
        dest_layout = QGridLayout(dest_group)

        dest_layout.addWidget(QLabel("Carpeta de Salida:"), 0, 0)
        self.txt_dir = QLineEdit(self.config.output_directory)
        btn_browse = QPushButton("Explorar...")
        btn_browse.clicked.connect(self._on_browse_dir)
        dest_layout.addWidget(self.txt_dir, 0, 1)
        dest_layout.addWidget(btn_browse, 0, 2)

        dest_layout.addWidget(QLabel("Nombre Base:"), 1, 0)
        self.txt_name = QLineEdit(self.config.base_name)
        dest_layout.addWidget(self.txt_name, 1, 1, 1, 2)

        main_layout.addWidget(dest_group)

        # 2. Format & Resolution
        fmt_group = QGroupBox("Formato y Resolución")
        fmt_layout = QGridLayout(fmt_group)

        fmt_layout.addWidget(QLabel("Formato de Imagen:"), 0, 0)
        self.combo_format = QComboBox()
        self.combo_format.addItems(["PNG (Sin perdida)", "TGA (Juegos / Motor 3D)", "AVIF (Alta compresion moderna)", "JPEG (Comprimido)", "TIFF"])
        self.combo_format.currentIndexChanged.connect(self._on_format_changed)
        fmt_layout.addWidget(self.combo_format, 0, 1)

        fmt_layout.addWidget(QLabel("Resolución:"), 1, 0)
        self.combo_res = QComboBox()
        self.combo_res.addItems([
            "Original (Sin cambios)",
            "512 x 512 (Baja)",
            "1024 x 1024 (1K)",
            "2048 x 2048 (2K - Recomendado)",
            "4096 x 4096 (4K Ultra HD)"
        ])
        fmt_layout.addWidget(self.combo_res, 1, 1)

        main_layout.addWidget(fmt_group)

        # 3. Maps Selection & Suffixes
        maps_group = QGroupBox("Mapas a Exportar y Sufijos de Archivo")
        maps_layout = QGridLayout(maps_group)

        self.map_checks = {}
        self.suffix_edits = {}

        row = 0
        map_labels = [
            ("albedo", "Albedo / Base Color", "_albedo", True),
            ("normal", "Normal Map", "_normal", True),
            ("height", "Height / Displacement", "_height", True),
            ("roughness", "Roughness Map", "_roughness", True),
            ("metallic", "Metallic Map", "_metallic", True),
            ("ao", "Ambient Occlusion (AO)", "_ao", True),
            ("specular", "Specular Map", "_specular", False),
            ("orm", "ORM Packed (AO+Rough+Metal)", "_orm", True),
        ]

        for key, label, default_suffix, checked in map_labels:
            chk = QCheckBox(label)
            chk.setChecked(checked)
            self.map_checks[key] = chk
            maps_layout.addWidget(chk, row, 0)

            txt = QLineEdit(default_suffix)
            txt.setFixedWidth(120)
            self.suffix_edits[key] = txt
            maps_layout.addWidget(txt, row, 1)

            row += 1

        main_layout.addWidget(maps_group)

        # 4. Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_export = QPushButton("Exportar Mapas PBR")
        btn_export.setObjectName("PrimaryButton")
        btn_export.setStyleSheet("QPushButton { background-color: #2563eb; color: #ffffff; font-weight: bold; padding: 8px 16px; border-radius: 5px; }")
        btn_export.clicked.connect(self._on_export)
        btn_layout.addWidget(btn_export)

        main_layout.addLayout(btn_layout)

    def _on_browse_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta de Exportación", self.txt_dir.text())
        if folder:
            self.txt_dir.setText(folder)

    def _on_format_changed(self, idx: int):
        formats = ["PNG", "TGA", "AVIF", "JPEG", "TIFF"]
        if idx < len(formats):
            self.config.format = formats[idx]

    def _on_export(self):
        out_dir = self.txt_dir.text().strip()
        if not out_dir:
            QMessageBox.warning(self, "Error", "Por favor selecciona una carpeta de salida valida.")
            return

        base_name = self.txt_name.text().strip()
        if not base_name:
            base_name = "material"

        self.config.output_directory = out_dir
        self.config.base_name = base_name

        # Update formats
        formats = ["PNG", "TGA", "AVIF", "JPEG", "TIFF"]
        idx = self.combo_format.currentIndex()
        self.config.format = formats[idx] if idx < len(formats) else "PNG"

        # Update resolution
        res_map = {
            0: None,
            1: (512, 512),
            2: (1024, 1024),
            3: (2048, 2048),
            4: (4096, 4096)
        }
        self.config.resolution = res_map.get(self.combo_res.currentIndex(), None)

        # Update enabled maps and suffixes
        for key in self.map_checks:
            self.config.enabled_maps[key] = self.map_checks[key].isChecked()
            self.config.suffixes[key] = self.suffix_edits[key].text().strip()

        try:
            saved = PBRExporter.export_all_maps(self.maps_dict, self.config)
            msg = f"¡Se han exportado {len(saved)} mapas PBR exitosamente en:\n{out_dir}\n\nArchivos creados:\n"
            for k, p in saved.items():
                msg += f"• {os.path.basename(p)}\n"
            QMessageBox.information(self, "Exportación Completada", msg)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error al Exportar", f"Ocurrió un error al guardar los mapas:\n{str(e)}")
