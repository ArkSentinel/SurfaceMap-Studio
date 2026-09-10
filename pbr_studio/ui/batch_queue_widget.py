"""
Batch Multi-Texture Queue Widget
Visual management for processing multiple textures simultaneously with individual presets and mass export.
"""

import os
from typing import List, Optional, Dict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QComboBox, QProgressBar, 
    QFileDialog, QMessageBox, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QImage, QColor, QFont, QIcon

from ..core.batch_manager import BatchManager, BatchMaterialItem
from ..core.presets import PresetManager
from ..core.projects import ProjectTarget
from .widgets import DropZoneWidget


class BatchItemWidget(QWidget):
    """Custom row widget inside the batch materials list."""
    presetChanged = pyqtSignal(str)
    deleteRequested = pyqtSignal()

    def __init__(self, item: BatchMaterialItem, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.item = item

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        # Thumbnail
        self.lbl_thumb = QLabel()
        self.lbl_thumb.setFixedSize(48, 48)
        self.lbl_thumb.setStyleSheet("background-color: #141517; border: 1px solid #373a40; border-radius: 4px;")
        self.lbl_thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_thumbnail()
        layout.addWidget(self.lbl_thumb)

        # Info column (Name, Dimensions, Status)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        self.lbl_name = QLabel(item.name)
        self.lbl_name.setStyleSheet("font-weight: bold; color: #f1f3f5; font-size: 12px;")
        info_layout.addWidget(self.lbl_name)

        w, h = item.dimensions
        self.lbl_sub = QLabel(f"{w}x{h} px | Estado: {item.status}")
        self.lbl_sub.setStyleSheet("color: #909296; font-size: 11px;")
        info_layout.addWidget(self.lbl_sub)

        layout.addLayout(info_layout, stretch=1)

        # Preset Selector
        self.combo_preset = QComboBox()
        self.combo_preset.addItems(PresetManager.get_preset_names())
        preset_idx = self.combo_preset.findText(item.preset_name)
        if preset_idx >= 0:
            self.combo_preset.setCurrentIndex(preset_idx)
        self.combo_preset.setFixedWidth(160)
        self.combo_preset.setStyleSheet("font-size: 11px; padding: 2px 4px;")
        self.combo_preset.currentIndexChanged.connect(self._on_preset_changed)
        layout.addWidget(self.combo_preset)

        # Delete button
        btn_del = QPushButton("X")
        btn_del.setFixedSize(24, 24)
        btn_del.setStyleSheet("QPushButton { color: #f87171; font-weight: bold; background: #202124; border: 1px solid #373a40; border-radius: 3px; } QPushButton:hover { background: #dc2626; color: #fff; }")
        btn_del.clicked.connect(self.deleteRequested.emit)
        layout.addWidget(btn_del)

    def _update_thumbnail(self):
        if self.item.thumbnail:
            data = self.item.thumbnail.convert("RGB").tobytes("raw", "RGB")
            w, h = self.item.thumbnail.size
            qimg = QImage(data, w, h, w * 3, QImage.Format.Format_RGB888)
            pix = QPixmap.fromImage(qimg).scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.lbl_thumb.setPixmap(pix)
        else:
            self.lbl_thumb.setText("IMG")

    def _on_preset_changed(self, idx: int):
        pname = self.combo_preset.currentText()
        self.item.apply_preset(pname)
        self.presetChanged.emit(pname)

    def update_status(self):
        w, h = self.item.dimensions
        color = "#34d399" if self.item.status in ("Generado", "Exportado") else "#909296"
        self.lbl_sub.setText(f"{w}x{h} px | Estado: <span style='color:{color};'>{self.item.status}</span>")


class BatchQueueWidget(QWidget):
    """Container for managing the multi-texture queue and batch actions."""
    materialSelected = pyqtSignal(BatchMaterialItem)
    batchCountChanged = pyqtSignal(int)

    def __init__(self, batch_manager: BatchManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.batch_manager = batch_manager
        self.active_project: Optional[ProjectTarget] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Multi-file drop zone
        self.drop_zone = DropZoneWidget(self)
        self.drop_zone.filesDropped.connect(self.add_files)
        self.drop_zone.clicked.connect(self._on_browse_files)
        layout.addWidget(self.drop_zone)

        # Batch Global Toolbar
        tb_layout = QHBoxLayout()
        tb_layout.setSpacing(6)

        btn_add = QPushButton("Agregar Imagenes...")
        btn_add.clicked.connect(self._on_browse_files)
        tb_layout.addWidget(btn_add)

        self.combo_global_preset = QComboBox()
        self.combo_global_preset.addItems(["Preset Global..."] + PresetManager.get_preset_names())
        self.combo_global_preset.currentIndexChanged.connect(self._on_apply_global_preset)
        tb_layout.addWidget(self.combo_global_preset)

        btn_clear = QPushButton("Limpiar")
        btn_clear.clicked.connect(self._on_clear_queue)
        tb_layout.addWidget(btn_clear)

        layout.addLayout(tb_layout)

        # List Widget
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(
            "QListWidget { background-color: #141517; border: 1px solid #27292e; border-radius: 6px; }"
            "QListWidget::item { border-bottom: 1px solid #202124; }"
            "QListWidget::item:selected { background-color: #25262b; }"
        )
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget, stretch=1)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("QProgressBar { border: 1px solid #373a40; border-radius: 4px; text-align: center; background: #141517; } QProgressBar::chunk { background-color: #2563eb; }")
        layout.addWidget(self.progress_bar)

        # Batch Export Action Button
        self.btn_batch_export = QPushButton("Exportar Todo el Lote al Proyecto")
        self.btn_batch_export.setObjectName("PrimaryButton")
        self.btn_batch_export.setStyleSheet("QPushButton { background-color: #2563eb; color: #ffffff; font-weight: bold; padding: 9px; border-radius: 5px; font-size: 13px; } QPushButton:hover { background-color: #1d4ed8; }")
        self.btn_batch_export.clicked.connect(self._on_export_batch)
        layout.addWidget(self.btn_batch_export)

    def set_active_project(self, project: ProjectTarget):
        self.active_project = project
        self.btn_batch_export.setText(f"Exportar Todo el Lote a [{project.name}]")

    def _on_files_dropped(self, file_path: str):
        self.add_files([file_path])

    def _on_browse_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Seleccionar Una o Varias Texturas",
            "",
            "Imagenes (*.png *.jpg *.jpeg *.avif *.tga *.bmp *.tif *.tiff *.webp);;Todos los archivos (*.*)"
        )
        if files:
            self.add_files(files)

    def add_files(self, file_paths: List[str]):
        new_items = self.batch_manager.add_files(file_paths)
        if new_items:
            for item in new_items:
                self._add_item_to_list(item)
            self.batchCountChanged.emit(len(self.batch_manager.items))
            # Auto select the last added item
            self.select_item(new_items[-1])

    def _add_item_to_list(self, item: BatchMaterialItem):
        list_item = QListWidgetItem(self.list_widget)
        list_item.setSizeHint(QSize(280, 62))
        list_item.setData(Qt.ItemDataRole.UserRole, item.id)

        row_widget = BatchItemWidget(item, self)
        row_widget.presetChanged.connect(lambda pname: self._on_item_preset_changed(item))
        row_widget.deleteRequested.connect(lambda: self._on_delete_item(item.id))

        self.list_widget.addItem(list_item)
        self.list_widget.setItemWidget(list_item, row_widget)

    def select_item(self, item: BatchMaterialItem):
        for i in range(self.list_widget.count()):
            l_item = self.list_widget.item(i)
            if l_item.data(Qt.ItemDataRole.UserRole) == item.id:
                self.list_widget.setCurrentItem(l_item)
                self.materialSelected.emit(item)
                break

    def _on_item_clicked(self, list_item: QListWidgetItem):
        item_id = list_item.data(Qt.ItemDataRole.UserRole)
        item = self.batch_manager.get_item(item_id)
        if item:
            self.materialSelected.emit(item)

    def _on_item_preset_changed(self, item: BatchMaterialItem):
        self._refresh_row_widget(item.id)
        if self.list_widget.currentItem() and self.list_widget.currentItem().data(Qt.ItemDataRole.UserRole) == item.id:
            self.materialSelected.emit(item)

    def _on_delete_item(self, item_id: str):
        self.batch_manager.remove_item(item_id)
        for i in range(self.list_widget.count()):
            l_item = self.list_widget.item(i)
            if l_item.data(Qt.ItemDataRole.UserRole) == item_id:
                self.list_widget.takeItem(i)
                break
        self.batchCountChanged.emit(len(self.batch_manager.items))
        if self.list_widget.count() > 0:
            first_id = self.list_widget.item(0).data(Qt.ItemDataRole.UserRole)
            item = self.batch_manager.get_item(first_id)
            if item:
                self.select_item(item)

    def _on_clear_queue(self):
        self.batch_manager.clear()
        self.list_widget.clear()
        self.batchCountChanged.emit(0)

    def _on_apply_global_preset(self, idx: int):
        if idx <= 0:
            return
        preset_name = self.combo_global_preset.currentText()
        for item in self.batch_manager.items:
            item.apply_preset(preset_name)
        # Refresh all row widgets
        for i in range(self.list_widget.count()):
            l_item = self.list_widget.item(i)
            item_id = l_item.data(Qt.ItemDataRole.UserRole)
            self._refresh_row_widget(item_id)
        self.combo_global_preset.setCurrentIndex(0)

        # Notify active
        if self.list_widget.currentItem():
            active_id = self.list_widget.currentItem().data(Qt.ItemDataRole.UserRole)
            active_item = self.batch_manager.get_item(active_id)
            if active_item:
                self.materialSelected.emit(active_item)

    def _refresh_row_widget(self, item_id: str):
        for i in range(self.list_widget.count()):
            l_item = self.list_widget.item(i)
            if l_item.data(Qt.ItemDataRole.UserRole) == item_id:
                w = self.list_widget.itemWidget(l_item)
                if isinstance(w, BatchItemWidget):
                    w.update_status()
                    # Sync combo
                    idx = w.combo_preset.findText(w.item.preset_name)
                    if idx >= 0 and w.combo_preset.currentIndex() != idx:
                        w.combo_preset.blockSignals(True)
                        w.combo_preset.setCurrentIndex(idx)
                        w.combo_preset.blockSignals(False)
                break

    def _on_export_batch(self):
        if not self.batch_manager.items:
            QMessageBox.warning(self, "Aviso", "No hay texturas en la cola para exportar.")
            return

        if not self.active_project:
            QMessageBox.warning(self, "Aviso", "Por favor selecciona un proyecto de destino en la barra superior.")
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(self.batch_manager.items))
        self.progress_bar.setValue(0)

        def on_prog(curr, total, name):
            self.progress_bar.setValue(curr)

        count = self.batch_manager.export_all_to_project(self.active_project, progress_callback=on_prog)

        # Refresh statuses
        for item in self.batch_manager.items:
            self._refresh_row_widget(item.id)

        self.progress_bar.setVisible(False)
        QMessageBox.information(
            self,
            "Lote Exportado",
            f"Se han generado y exportado con exito {count} materiales PBR hacia:\n{self.active_project.destination_path}"
        )
