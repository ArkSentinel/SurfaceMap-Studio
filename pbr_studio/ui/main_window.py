"""
PBR Material Studio - Main Application Window
Coordinates multi-texture batch management, project destination targeting (Godot, Blender, Unreal, Unity),
mathematical map generation, 2D/3D previews, and customized workflows.
"""

import os
import time
from typing import Optional, Dict, List
import numpy as np
from PIL import Image

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
    QFileDialog, QMessageBox, QStatusBar, QLabel, QToolBar, 
    QComboBox, QPushButton, QTabWidget, QToolButton
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QIcon, QKeySequence

from ..core.pbr_engine import PBREngine, PBRMapSettings
from ..core.presets import PresetManager
from ..core.projects import ProjectTarget, ProjectManager
from ..core.batch_manager import BatchManager, BatchMaterialItem
from .settings_panel import SettingsPanel
from .preview_2d import Preview2DWidget
from .preview_3d import Preview3DWidget
from .export_dialog import ExportDialog
from .project_dialog import ProjectManagerDialog
from .batch_queue_widget import BatchQueueWidget


class MainWindow(QMainWindow):
    """Main window for PBR Material Studio application."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SurfaceMap Studio - Generador de Mapas PBR y Superficies")
        self.resize(1380, 880)
        self.setMinimumSize(1000, 660)

        # Core state
        self.projects: List[ProjectTarget] = ProjectManager.load_projects()
        self.active_project: Optional[ProjectTarget] = self._get_initial_project()
        
        self.batch_manager = BatchManager()
        self.active_material_item: Optional[BatchMaterialItem] = None

        self.settings = PBRMapSettings()
        self.current_image_path: Optional[str] = None
        self.current_albedo: Optional[np.ndarray] = None
        self.generated_maps: Dict[str, np.ndarray] = {}

        # Debounce timer for smooth slider updates
        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(True)
        self._update_timer.setInterval(40)  # 40ms debounce
        self._update_timer.timeout.connect(self._recalculate_maps)

        self._init_ui()
        self._init_menus()
        self._create_sample_texture()

    def _get_initial_project(self) -> Optional[ProjectTarget]:
        if not self.projects:
            return None
        for p in self.projects:
            if p.is_default:
                return p
        return self.projects[0]

    def _init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Toolbar
        self._init_toolbar()

        # Main horizontal splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setHandleWidth(2)

        # Left Sidebar with Tabs (Settings & Batch Queue)
        self.sidebar_tabs = QTabWidget()
        self.sidebar_tabs.setStyleSheet(
            "QTabWidget::pane { border: 1px solid #27292e; background-color: #18191c; border-radius: 4px; }"
            "QTabBar::tab { font-size: 11px; padding: 6px 14px; }"
        )
        self.sidebar_tabs.setMinimumWidth(360)
        self.sidebar_tabs.setMaximumWidth(480)

        # Tab 1: Settings Panel
        self.settings_panel = SettingsPanel(self.settings, self.sidebar_tabs)
        self.settings_panel.settingsChanged.connect(self._on_settings_changed)
        self.settings_panel.presetChanged.connect(self._on_settings_panel_preset_changed)
        self.sidebar_tabs.addTab(self.settings_panel, "Ajustes de Material")

        # Tab 2: Batch Queue
        self.batch_widget = BatchQueueWidget(self.batch_manager, self.sidebar_tabs)
        self.batch_widget.materialSelected.connect(self._on_batch_material_selected)
        self.batch_widget.batchCountChanged.connect(self._on_batch_count_changed)
        if self.active_project:
            self.batch_widget.set_active_project(self.active_project)
        self.sidebar_tabs.addTab(self.batch_widget, "Cola de Lote (0)")

        main_splitter.addWidget(self.sidebar_tabs)

        # Right Panel (2D and 3D Viewports)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(4, 6, 6, 6)
        right_layout.setSpacing(6)

        # Split viewports horizontally
        view_splitter = QSplitter(Qt.Orientation.Horizontal)
        view_splitter.setHandleWidth(2)

        # 2D Preview Widget
        self.preview_2d = Preview2DWidget(view_splitter)
        view_splitter.addWidget(self.preview_2d)

        # 3D Preview Widget
        self.preview_3d = Preview3DWidget(view_splitter)
        view_splitter.addWidget(self.preview_3d)

        # 65% 2D, 35% 3D
        view_splitter.setSizes([780, 420])

        right_layout.addWidget(view_splitter, stretch=1)
        main_splitter.addWidget(right_panel)

        main_splitter.setSizes([400, 980])
        main_layout.addWidget(main_splitter)

        # Status Bar
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        
        self.lbl_status_info = QLabel("Listo. Arrastra una textura o agrega archivos al lote para comenzar.")
        self.lbl_status_dest = QLabel("")
        self.lbl_status_dest.setStyleSheet("color: #34d399; font-weight: 500; margin-right: 16px;")
        self.lbl_status_dim = QLabel("")
        self.lbl_status_dim.setStyleSheet("color: #60a5fa; font-weight: bold; margin-right: 12px;")
        
        self.status_bar.addWidget(self.lbl_status_info, 1)
        self.status_bar.addPermanentWidget(self.lbl_status_dest)
        self.status_bar.addPermanentWidget(self.lbl_status_dim)

        self._update_status_dest()

    def _init_toolbar(self):
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Open button
        btn_open = QPushButton("Abrir Textura")
        btn_open.clicked.connect(self.open_file_dialog)
        toolbar.addWidget(btn_open)

        btn_batch = QPushButton("Cargar Lote...")
        btn_batch.clicked.connect(self._open_batch_dialog)
        toolbar.addWidget(btn_batch)

        toolbar.addSeparator()

        # Project Target Quick Selector
        lbl_proj = QLabel(" Destino de Proyecto: ")
        lbl_proj.setStyleSheet("color: #909296; font-weight: 500;")
        toolbar.addWidget(lbl_proj)

        self.tb_project_combo = QComboBox()
        self.tb_project_combo.setMinimumWidth(220)
        self._refresh_project_combo()
        self.tb_project_combo.currentIndexChanged.connect(self._on_toolbar_project_changed)
        toolbar.addWidget(self.tb_project_combo)

        btn_manage_proj = QPushButton("Gestionar...")
        btn_manage_proj.setToolTip("Configurar carpetas de proyectos para Godot, Blender, Unreal, Unity")
        btn_manage_proj.clicked.connect(self.open_project_manager)
        toolbar.addWidget(btn_manage_proj)

        # Quick Export to Active Project
        self.btn_quick_export = QPushButton("Exportar al Proyecto")
        self.btn_quick_export.setObjectName("PrimaryButton")
        self.btn_quick_export.setStyleSheet("QPushButton { background-color: #2563eb; color: #ffffff; font-weight: bold; border-radius: 4px; padding: 6px 14px; }")
        self.btn_quick_export.setToolTip("Exporta instantaneamente el material activo a la carpeta del proyecto seleccionado")
        self.btn_quick_export.clicked.connect(self.export_to_active_project)
        toolbar.addWidget(self.btn_quick_export)

        btn_export_dialog = QPushButton("Exportar Mas Opciones...")
        btn_export_dialog.clicked.connect(self.open_export_dialog)
        toolbar.addWidget(btn_export_dialog)

        toolbar.addSeparator()

        # Preset Quick Bar
        lbl_p = QLabel(" Preset: ")
        lbl_p.setStyleSheet("color: #909296;")
        toolbar.addWidget(lbl_p)

        self.tb_preset_combo = QComboBox()
        self.tb_preset_combo.addItems(PresetManager.get_preset_names())
        self.tb_preset_combo.currentIndexChanged.connect(self._on_toolbar_preset_changed)
        toolbar.addWidget(self.tb_preset_combo)

    def _init_menus(self):
        menubar = self.menuBar()

        # Archivo Menu
        menu_file = menubar.addMenu("Archivo")

        act_open = QAction("Abrir Textura...", self)
        act_open.setShortcut(QKeySequence("Ctrl+O"))
        act_open.triggered.connect(self.open_file_dialog)
        menu_file.addAction(act_open)

        act_open_batch = QAction("Cargar Lote de Texturas...", self)
        act_open_batch.setShortcut(QKeySequence("Ctrl+Shift+O"))
        act_open_batch.triggered.connect(self._open_batch_dialog)
        menu_file.addAction(act_open_batch)

        menu_file.addSeparator()

        act_quick_exp = QAction("Exportar al Proyecto Activo", self)
        act_quick_exp.setShortcut(QKeySequence("Ctrl+S"))
        act_quick_exp.triggered.connect(self.export_to_active_project)
        menu_file.addAction(act_quick_exp)

        act_export = QAction("Exportar Material PBR (Opciones)...", self)
        act_export.setShortcut(QKeySequence("Ctrl+E"))
        act_export.triggered.connect(self.open_export_dialog)
        menu_file.addAction(act_export)

        menu_file.addSeparator()

        act_projects = QAction("Gestion de Proyectos...", self)
        act_projects.setShortcut(QKeySequence("Ctrl+P"))
        act_projects.triggered.connect(self.open_project_manager)
        menu_file.addAction(act_projects)

        menu_file.addSeparator()

        act_exit = QAction("Salir", self)
        act_exit.setShortcut(QKeySequence("Ctrl+Q"))
        act_exit.triggered.connect(self.close)
        menu_file.addAction(act_exit)

        # Ver Menu
        menu_view = menubar.addMenu("Ver")
        
        act_fit = QAction("Ajustar Vista 2D", self)
        act_fit.setShortcut(QKeySequence("Ctrl+F"))
        act_fit.triggered.connect(self.preview_2d._on_fit_clicked)
        menu_view.addAction(act_fit)

        act_actual = QAction("Tamano Real 100%", self)
        act_actual.setShortcut(QKeySequence("Ctrl+1"))
        act_actual.triggered.connect(self.preview_2d._on_actual_clicked)
        menu_view.addAction(act_actual)

        # Ayuda Menu
        menu_help = menubar.addMenu("Ayuda")
        act_about = QAction("Acerca de PBR Material Studio", self)
        act_about.triggered.connect(self._show_about)
        menu_help.addAction(act_about)

    def _refresh_project_combo(self):
        self.tb_project_combo.blockSignals(True)
        self.tb_project_combo.clear()
        for p in self.projects:
            self.tb_project_combo.addItem(f"{p.name} ({p.engine_type})", p)
        
        if self.active_project:
            for i in range(self.tb_project_combo.count()):
                p = self.tb_project_combo.itemData(i)
                if p and p.name == self.active_project.name:
                    self.tb_project_combo.setCurrentIndex(i)
                    break
        self.tb_project_combo.blockSignals(False)

    def _on_toolbar_project_changed(self, idx: int):
        if idx >= 0:
            self.active_project = self.tb_project_combo.itemData(idx)
            self._update_status_dest()
            if self.active_project:
                self.batch_widget.set_active_project(self.active_project)

    def _update_status_dest(self):
        if self.active_project:
            self.lbl_status_dest.setText(f"Destino: {self.active_project.name} -> {self.active_project.destination_path}")
        else:
            self.lbl_status_dest.setText("")

    def open_project_manager(self):
        dialog = ProjectManagerDialog(self)
        dialog.projectsUpdated.connect(self._on_projects_updated)
        dialog.exec()

    def _on_projects_updated(self):
        self.projects = ProjectManager.load_projects()
        self.active_project = self._get_initial_project()
        self._refresh_project_combo()
        self._update_status_dest()
        if self.active_project:
            self.batch_widget.set_active_project(self.active_project)

    def _create_sample_texture(self):
        """Creates a default procedural stone/brick texture."""
        h, w = 512, 512
        y, x = np.mgrid[0:h, 0:w]
        
        fx = np.sin(x * 0.05) * np.cos(y * 0.05) * 0.3
        pattern = np.sin(x * 0.02) * np.sin(y * 0.02) + fx
        noise = np.random.RandomState(42).uniform(-0.15, 0.15, (h, w)).astype(np.float32)
        base = np.clip((pattern * 0.4 + 0.5) + noise, 0.0, 1.0)
        
        sample_rgb = np.zeros((h, w, 3), dtype=np.float32)
        sample_rgb[:, :, 0] = np.clip(base * 0.85 + 0.1, 0.0, 1.0)
        sample_rgb[:, :, 1] = np.clip(base * 0.72 + 0.08, 0.0, 1.0)
        sample_rgb[:, :, 2] = np.clip(base * 0.60 + 0.05, 0.0, 1.0)

        self.current_albedo = sample_rgb
        self.current_image_path = "sample_stone_texture.png"
        self._recalculate_maps()
        self.lbl_status_dim.setText(f"{w} x {h} px")
        self.lbl_status_info.setText("Textura de muestra cargada. Arrastra una o varias imagenes para comenzar.")

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Textura Base",
            "",
            "Imagenes (*.png *.jpg *.jpeg *.avif *.tga *.bmp *.tif *.tiff *.webp);;Todos los archivos (*.*)"
        )
        if file_path:
            self.load_image(file_path)

    def _open_batch_dialog(self):
        self.sidebar_tabs.setCurrentIndex(1)  # Switch to batch tab
        self.batch_widget._on_browse_files()

    def load_image(self, file_path: str):
        """Loads and processes an input texture file and registers it into the batch queue."""
        if not os.path.exists(file_path):
            QMessageBox.critical(self, "Error", f"El archivo no existe:\n{file_path}")
            return

        try:
            arr = PBREngine.load_image(file_path)
            self.current_image_path = file_path
            self.current_albedo = arr
            h, w = arr.shape[:2]
            
            self.lbl_status_dim.setText(f"{w} x {h} px")
            self.lbl_status_info.setText(f"Cargado: {os.path.basename(file_path)}")
            
            self._recalculate_maps()
            self.preview_2d.viewport.reset_view()

            # Add to batch queue
            self.batch_widget.add_files([file_path])

        except Exception as e:
            QMessageBox.critical(self, "Error al Cargar", f"No se pudo cargar la imagen:\n{str(e)}")

    def _on_batch_material_selected(self, item: BatchMaterialItem):
        """Called when user selects a material from the batch queue list."""
        self.active_material_item = item
        self.current_image_path = item.file_path
        self.current_albedo = item.albedo_arr
        self.settings = item.settings
        self.settings_panel.settings = self.settings
        self.settings_panel.sync_ui_from_settings()

        h, w = item.dimensions[1], item.dimensions[0]
        self.lbl_status_dim.setText(f"{w} x {h} px")
        self.lbl_status_info.setText(f"Editando material: {item.name}")

        self._recalculate_maps()
        self.preview_2d.viewport.reset_view()

    def _on_batch_count_changed(self, count: int):
        self.sidebar_tabs.setTabText(1, f"Cola de Lote ({count})")

    def _on_settings_changed(self):
        """Triggered when any slider or checkbox is modified in the settings panel."""
        self._update_timer.start()

    def _on_toolbar_preset_changed(self, idx: int):
        preset_name = self.tb_preset_combo.currentText()
        if self.settings_panel.preset_combo.currentText() != preset_name:
            self.settings_panel.preset_combo.blockSignals(True)
            self.settings_panel.preset_combo.setCurrentText(preset_name)
            self.settings_panel.preset_combo.blockSignals(False)
        if PresetManager.apply_preset(self.settings, preset_name):
            self.settings_panel.sync_ui_from_settings()
            if self.active_material_item:
                self.active_material_item.preset_name = preset_name
            self._recalculate_maps()

    def _on_settings_panel_preset_changed(self, preset_name: str):
        if self.tb_preset_combo.currentText() != preset_name:
            self.tb_preset_combo.blockSignals(True)
            self.tb_preset_combo.setCurrentText(preset_name)
            self.tb_preset_combo.blockSignals(False)
        if self.active_material_item:
            self.active_material_item.preset_name = preset_name

    def _recalculate_maps(self):
        """Re-runs the PBR generation engine for all maps with current settings."""
        if self.current_albedo is None:
            return

        t0 = time.time()
        self.generated_maps = PBREngine.generate_all_maps(self.current_albedo, self.settings)
        dt = (time.time() - t0) * 1000.0

        if self.active_material_item:
            self.active_material_item.generated_maps = self.generated_maps
            self.active_material_item.status = "Generado"

        # Update 2D and 3D preview widgets
        self.preview_2d.update_maps(self.generated_maps)
        self.preview_3d.update_maps(self.generated_maps)

        filename = os.path.basename(self.current_image_path) if self.current_image_path else "muestra"
        self.lbl_status_info.setText(f"Mapas PBR generados en {dt:.1f} ms | Material: {filename}")

    def export_to_active_project(self):
        """1-Click instant export to the configured active project destination."""
        if not self.active_project:
            self.open_project_manager()
            return

        if not self.generated_maps:
            QMessageBox.warning(self, "Aviso", "No hay mapas generados para exportar.")
            return

        mat_name = os.path.splitext(os.path.basename(self.current_image_path))[0] if self.current_image_path else "material"
        
        item = self.active_material_item or BatchMaterialItem(self.current_image_path or "material.png")
        item.name = mat_name
        item.generated_maps = self.generated_maps
        item.albedo_arr = self.current_albedo
        item.settings = self.settings

        try:
            saved = item.export_to_project(self.active_project)
            out_path = os.path.dirname(list(saved.values())[0]) if saved else self.active_project.destination_path
            
            msg = f"Material '{mat_name}' exportado con exito hacia [{self.active_project.name}]:\n{out_path}\n\nArchivos guardados:\n"
            for k, p in saved.items():
                msg += f"- {os.path.basename(p)}\n"
            QMessageBox.information(self, "Exportacion Exitosa", msg)
        except Exception as e:
            QMessageBox.critical(self, "Error al Exportar", f"No se pudo exportar el material:\n{str(e)}")

    def open_export_dialog(self):
        """Opens the custom export configuration dialog."""
        if not self.generated_maps:
            QMessageBox.warning(self, "Aviso", "No hay mapas generados para exportar.")
            return

        default_dir = self.active_project.destination_path if self.active_project else (
            os.path.dirname(self.current_image_path) if self.current_image_path and os.path.exists(self.current_image_path) else ""
        )
        default_name = os.path.splitext(os.path.basename(self.current_image_path))[0] if self.current_image_path else "material"

        dialog = ExportDialog(self.generated_maps, default_dir=default_dir, default_name=default_name, parent=self)
        dialog.exec()

    def _show_about(self):
        QMessageBox.about(
            self,
            "Acerca de SurfaceMap Studio",
            "<b>SurfaceMap Studio v1.2.0</b><br><br>"
            "Aplicacion profesional de computacion grafica para derivar y generar sets completos de mapas PBR "
            "(Normal, Height, Roughness, Metallic, AO, Specular, ORM Packed) con procesamiento individual y por lotes.<br><br>"
            "Gestion integrada de destinos para <b>Godot 4</b>, <b>Blender</b>, <b>Unreal Engine 5</b> y <b>Unity</b>.<br>"
            "Desarrollado en Python con PyQt6 y NumPy."
        )
