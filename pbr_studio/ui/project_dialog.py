"""
Project Destination Management Dialog
Create, configure, and manage target destinations for Godot, Blender, Unreal Engine, Unity, and custom game projects.
"""

import os
from typing import List, Optional
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
    QListWidgetItem, QLabel, QLineEdit, QPushButton, QComboBox, 
    QCheckBox, QFileDialog, QGroupBox, QGridLayout, QMessageBox, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from ..core.projects import ProjectTarget, ProjectManager


class ProjectManagerDialog(QDialog):
    """Dialog for managing project export targets."""
    projectsUpdated = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Gestion de Proyectos y Destinos de Exportacion")
        self.resize(760, 480)
        self.setMinimumSize(640, 400)
        self.setStyleSheet("background-color: #1a1b1e; color: #e4e5e7;")

        self.projects: List[ProjectTarget] = ProjectManager.load_projects()
        self.current_project: Optional[ProjectTarget] = None
        self._block_updates = False

        self._init_ui()
        self._load_project_list()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(12)

        header_lbl = QLabel("Configura las carpetas de tus proyectos (Godot, Blender, Unreal, Unity) para exportar directamente con 1 solo clic.")
        header_lbl.setStyleSheet("color: #909296; font-size: 12px;")
        main_layout.addWidget(header_lbl)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left Column: List & action buttons
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 8, 0)
        left_layout.setSpacing(8)

        lbl_list = QLabel("Proyectos Guardados:")
        lbl_list.setStyleSheet("font-weight: bold; color: #60a5fa;")
        left_layout.addWidget(lbl_list)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(
            "QListWidget { background-color: #141517; border: 1px solid #27292e; border-radius: 6px; padding: 4px; }"
            "QListWidget::item { padding: 8px 10px; border-radius: 4px; margin-bottom: 2px; }"
            "QListWidget::item:selected { background-color: #2563eb; color: #ffffff; font-weight: 600; }"
            "QListWidget::item:hover:!selected { background-color: #25262b; }"
        )
        self.list_widget.currentRowChanged.connect(self._on_project_selected)
        left_layout.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        btn_add = QPushButton("Nuevo")
        btn_add.clicked.connect(self._on_add_project)
        btn_dup = QPushButton("Duplicar")
        btn_dup.clicked.connect(self._on_duplicate_project)
        btn_del = QPushButton("Eliminar")
        btn_del.clicked.connect(self._on_delete_project)

        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_dup)
        btn_row.addWidget(btn_del)
        left_layout.addLayout(btn_row)

        splitter.addWidget(left_widget)

        # Right Column: Details editor
        right_widget = QWidget()
        self.right_layout = QVBoxLayout(right_widget)
        self.right_layout.setContentsMargins(8, 0, 0, 0)
        self.right_layout.setSpacing(10)

        # Details GroupBox
        self.details_group = QGroupBox("Configuracion del Proyecto")
        form_layout = QGridLayout(self.details_group)
        form_layout.setSpacing(10)

        # Name
        form_layout.addWidget(QLabel("Nombre del Proyecto:"), 0, 0)
        self.txt_name = QLineEdit()
        self.txt_name.textChanged.connect(self._on_field_changed)
        form_layout.addWidget(self.txt_name, 0, 1, 1, 2)

        # Engine Type
        form_layout.addWidget(QLabel("Motor / Software Objetivo:"), 1, 0)
        self.combo_engine = QComboBox()
        self.combo_engine.addItems(["Godot 4", "Blender", "Unreal Engine 5", "Unity", "Personalizado"])
        self.combo_engine.currentIndexChanged.connect(self._on_engine_changed)
        form_layout.addWidget(self.combo_engine, 1, 1, 1, 2)

        # Destination Directory
        form_layout.addWidget(QLabel("Ruta de la Carpeta Destino:"), 2, 0)
        self.txt_path = QLineEdit()
        self.txt_path.textChanged.connect(self._on_field_changed)
        btn_browse = QPushButton("Examinar...")
        btn_browse.clicked.connect(self._on_browse_folder)
        form_layout.addWidget(self.txt_path, 2, 1)
        form_layout.addWidget(btn_browse, 2, 2)

        # Format
        form_layout.addWidget(QLabel("Formato de Texturas:"), 3, 0)
        self.combo_format = QComboBox()
        self.combo_format.addItems(["PNG", "TGA", "AVIF", "JPEG", "TIFF"])
        self.combo_format.currentIndexChanged.connect(self._on_field_changed)
        form_layout.addWidget(self.combo_format, 3, 1, 1, 2)

        # Format specifics
        self.chk_orm = QCheckBox("Empaquetar textura ORM (AO en R, Roughness en G, Metallic en B)")
        self.chk_orm.toggled.connect(self._on_field_changed)
        form_layout.addWidget(self.chk_orm, 4, 0, 1, 3)

        self.chk_directx = QCheckBox("Formato Normal DirectX (Invertir canal Y / Verde para Unreal)")
        self.chk_directx.toggled.connect(self._on_field_changed)
        form_layout.addWidget(self.chk_directx, 5, 0, 1, 3)

        self.chk_subfolder = QCheckBox("Crear subcarpeta individual por cada material (recomendado)")
        self.chk_subfolder.toggled.connect(self._on_field_changed)
        form_layout.addWidget(self.chk_subfolder, 6, 0, 1, 3)

        self.chk_default = QCheckBox("Establecer como proyecto predeterminado al iniciar")
        self.chk_default.toggled.connect(self._on_default_toggled)
        form_layout.addWidget(self.chk_default, 7, 0, 1, 3)

        self.right_layout.addWidget(self.details_group)
        self.right_layout.addStretch()

        splitter.addWidget(right_widget)
        splitter.setSizes([260, 480])
        main_layout.addWidget(splitter, stretch=1)

        # Bottom buttons
        bottom_row = QHBoxLayout()
        bottom_row.addStretch()

        btn_save = QPushButton("Guardar y Cerrar")
        btn_save.setObjectName("PrimaryButton")
        btn_save.setStyleSheet("QPushButton { background-color: #2563eb; color: #ffffff; font-weight: bold; padding: 7px 18px; border-radius: 4px; }")
        btn_save.clicked.connect(self._on_save_all)
        bottom_row.addWidget(btn_save)

        main_layout.addLayout(bottom_row)

    def _load_project_list(self):
        self._block_updates = True
        self.list_widget.clear()
        for p in self.projects:
            item = QListWidgetItem(f"{p.name} ({p.engine_type})")
            if p.is_default:
                item.setText(f"[Predeterminado] {item.text()}")
            self.list_widget.addItem(item)
        self._block_updates = False

        if self.projects:
            self.list_widget.setCurrentRow(0)

    def _on_project_selected(self, row: int):
        if self._block_updates or row < 0 or row >= len(self.projects):
            return

        self._block_updates = True
        p = self.projects[row]
        self.current_project = p

        self.txt_name.setText(p.name)
        engine_idx = self.combo_engine.findText(p.engine_type)
        if engine_idx >= 0:
            self.combo_engine.setCurrentIndex(engine_idx)
        else:
            self.combo_engine.setCurrentIndex(4)  # Personalizado

        self.txt_path.setText(p.destination_path)
        
        fmt_idx = self.combo_format.findText(p.format)
        if fmt_idx >= 0:
            self.combo_format.setCurrentIndex(fmt_idx)

        self.chk_orm.setChecked(p.pack_orm)
        self.chk_directx.setChecked(p.normal_directx)
        self.chk_subfolder.setChecked(p.subfolder_per_material)
        self.chk_default.setChecked(p.is_default)

        self._block_updates = False

    def _on_engine_changed(self, idx: int):
        if self._block_updates or not self.current_project:
            return
        engine = self.combo_engine.currentText()
        if engine == "Godot 4":
            self.chk_orm.setChecked(True)
            self.chk_directx.setChecked(False)
            self.combo_format.setCurrentText("PNG")
        elif engine == "Blender":
            self.chk_orm.setChecked(True)
            self.chk_directx.setChecked(False)
            self.combo_format.setCurrentText("PNG")
        elif engine == "Unreal Engine 5":
            self.chk_orm.setChecked(True)
            self.chk_directx.setChecked(True)
            self.combo_format.setCurrentText("PNG")
        elif engine == "Unity":
            self.chk_orm.setChecked(True)
            self.chk_directx.setChecked(False)
            self.combo_format.setCurrentText("PNG")
        self._on_field_changed()

    def _on_field_changed(self):
        if self._block_updates or not self.current_project:
            return
        self.current_project.name = self.txt_name.text().strip() or "Sin nombre"
        self.current_project.engine_type = self.combo_engine.currentText()
        self.current_project.destination_path = self.txt_path.text().strip()
        self.current_project.format = self.combo_format.currentText()
        self.current_project.pack_orm = self.chk_orm.isChecked()
        self.current_project.normal_directx = self.chk_directx.isChecked()
        self.current_project.subfolder_per_material = self.chk_subfolder.isChecked()
        self.current_project.is_default = self.chk_default.isChecked()

        # Update list item title
        row = self.list_widget.currentRow()
        if row >= 0:
            prefix = "[Predeterminado] " if self.current_project.is_default else ""
            self.list_widget.item(row).setText(f"{prefix}{self.current_project.name} ({self.current_project.engine_type})")

    def _on_default_toggled(self, checked: bool):
        if self._block_updates or not self.current_project:
            return
        if checked:
            for p in self.projects:
                p.is_default = (p == self.current_project)
            self._load_project_list()
        else:
            self.current_project.is_default = False
        self._on_field_changed()

    def _on_browse_folder(self):
        curr = self.txt_path.text() or os.path.expanduser("~/Desktop")
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta de Destino", curr)
        if folder:
            self.txt_path.setText(folder)

    def _on_add_project(self):
        desktop = os.path.expanduser("~/Desktop")
        new_p = ProjectTarget(
            name=f"Nuevo Proyecto {len(self.projects) + 1}",
            destination_path=os.path.join(desktop, f"Materiales_{len(self.projects) + 1}"),
            engine_type="Godot 4",
            format="PNG",
            pack_orm=True,
            normal_directx=False,
            subfolder_per_material=True,
            is_default=False
        )
        self.projects.append(new_p)
        self._load_project_list()
        self.list_widget.setCurrentRow(len(self.projects) - 1)

    def _on_duplicate_project(self):
        if not self.current_project:
            return
        dup_data = self.current_project.to_dict()
        dup_data["name"] += " (Copia)"
        dup_data["is_default"] = False
        dup_p = ProjectTarget.from_dict(dup_data)
        self.projects.append(dup_p)
        self._load_project_list()
        self.list_widget.setCurrentRow(len(self.projects) - 1)

    def _on_delete_project(self):
        if not self.current_project:
            return
        if len(self.projects) <= 1:
            QMessageBox.warning(self, "Aviso", "Debe mantenerse al menos un proyecto configurado.")
            return
        
        reply = QMessageBox.question(
            self,
            "Confirmar Eliminacion",
            f"¿Deseas eliminar el proyecto '{self.current_project.name}' de la lista?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            idx = self.list_widget.currentRow()
            self.projects.remove(self.current_project)
            self._load_project_list()
            new_idx = max(0, min(idx, len(self.projects) - 1))
            self.list_widget.setCurrentRow(new_idx)

    def _on_save_all(self):
        ProjectManager.save_projects(self.projects)
        self.projectsUpdated.emit()
        self.accept()
